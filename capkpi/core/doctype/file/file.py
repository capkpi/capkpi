# Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

"""
record of files

naming for same name files: file.gif, file-1.gif, file-2.gif etc
"""

from __future__ import unicode_literals

import base64
import hashlib
import imghdr
import io
import json
import mimetypes
import os
import re
import shutil
import zipfile
from typing import TYPE_CHECKING, Tuple

import requests
from PIL import Image, ImageFile, ImageOps
from requests.exceptions import HTTPError, SSLError
from six import PY2, BytesIO, string_types, text_type
from six.moves.urllib.parse import quote, unquote

import capkpi
from capkpi import _, conf, safe_decode
from capkpi.model.document import Document
from capkpi.utils import (
	call_hook_method,
	cint,
	cstr,
	encode,
	get_files_path,
	get_hook_method,
	get_url,
	random_string,
	strip,
)
from capkpi.utils.image import strip_exif_data

if TYPE_CHECKING:
	from PIL.ImageFile import ImageFile
	from requests.models import Response


class MaxFileSizeReachedError(capkpi.ValidationError):
	pass


class FolderNotEmpty(capkpi.ValidationError):
	pass


exclude_from_linked_with = True
ImageFile.LOAD_TRUNCATED_IMAGES = True
URL_PREFIXES = ("http://", "https://")


class File(Document):
	no_feed_on_delete = True

	@property
	def is_remote_file(self):
		if self.file_url:
			return self.file_url.startswith(URL_PREFIXES)
		return not self.content

	def before_insert(self):
		capkpi.local.rollback_observers.append(self)
		self.set_folder_name()
		if self.file_name:
			self.file_name = re.sub(r"/", "", self.file_name)
		self.content = self.get("content", None)
		self.decode = self.get("decode", False)

		if self.is_folder:
			return

		if self.is_remote_file:
			self.validate_remote_file()

		if self.content:
			self.save_file(content=self.content, decode=self.decode)

	def get_name_based_on_parent_folder(self):
		if self.folder:
			return "/".join([self.folder, self.file_name])

	def autoname(self):
		"""Set name for folder"""
		if self.is_folder:
			if self.folder:
				self.name = self.get_name_based_on_parent_folder()
			else:
				# home
				self.name = self.file_name
		else:
			self.name = capkpi.generate_hash("", 10)

	def after_insert(self):
		if not self.is_folder:
			self.add_comment_in_reference_doc(
				"Attachment",
				_("Added {0}").format(
					"<a href='{file_url}' target='_blank'>{file_name}</a>{icon}".format(
						**{
							"icon": ' <i class="fa fa-lock text-warning"></i>' if self.is_private else "",
							"file_url": quote(capkpi.safe_encode(self.file_url)) if self.file_url else self.file_name,
							"file_name": self.file_name or self.file_url,
						}
					)
				),
			)

	def after_rename(self, olddn, newdn, merge=False):
		for successor in self.get_successor():
			setup_folder_path(successor[0], self.name)

	def get_successor(self):
		return capkpi.db.get_values(doctype="File", filters={"folder": self.name}, fieldname="name")

	def validate(self):
		if self.is_new():
			self.set_is_private()
			self.set_file_name()
			self.validate_duplicate_entry()
			self.validate_attachment_limit()

		self.validate_folder()

		if self.is_folder:
			self.file_url = ""
		else:
			self.validate_url()

		self.file_size = capkpi.form_dict.file_size or self.file_size

	def validate_url(self):
		if not self.file_url or self.file_url.startswith(("http://", "https://")):
			if not self.flags.ignore_file_validate:
				self.validate_file()

			return

		# Probably an invalid web URL
		if not self.file_url.startswith(("/files/", "/private/files/")):
			capkpi.throw(_("URL must start with http:// or https://"), title=_("Invalid URL"))

		# Ensure correct formatting and type
		self.file_url = unquote(self.file_url)
		self.is_private = cint(self.is_private)

		self.handle_is_private_changed()

		base_path = os.path.realpath(get_files_path(is_private=self.is_private))
		if not os.path.realpath(self.get_full_path()).startswith(base_path):
			capkpi.throw(_("The File URL you've entered is incorrect"), title=_("Invalid File URL"))

	def handle_is_private_changed(self):
		if not capkpi.db.exists("File", {"name": self.name, "is_private": cint(not self.is_private)}):
			return

		old_file_url = self.file_url

		file_name = self.file_url.split("/")[-1]
		private_file_path = capkpi.get_site_path("private", "files", file_name)
		public_file_path = capkpi.get_site_path("public", "files", file_name)

		if self.is_private:
			shutil.move(public_file_path, private_file_path)
			url_starts_with = "/private/files/"
		else:
			shutil.move(private_file_path, public_file_path)
			url_starts_with = "/files/"

		self.file_url = "{0}{1}".format(url_starts_with, file_name)
		update_existing_file_docs(self)

		if (
			not self.attached_to_doctype
			or not self.attached_to_name
			or not self.fetch_attached_to_field(old_file_url)
		):
			return

		capkpi.db.set_value(
			self.attached_to_doctype, self.attached_to_name, self.attached_to_field, self.file_url
		)

	def fetch_attached_to_field(self, old_file_url):
		if self.attached_to_field:
			return True

		reference_dict = capkpi.get_doc(self.attached_to_doctype, self.attached_to_name).as_dict()

		for key, value in reference_dict.items():
			if value == old_file_url:
				self.attached_to_field = key
				return True

	def validate_attachment_limit(self):
		attachment_limit = 0
		if self.attached_to_doctype and self.attached_to_name:
			attachment_limit = cint(capkpi.get_meta(self.attached_to_doctype).max_attachments)

		if attachment_limit:
			current_attachment_count = len(
				capkpi.get_all(
					"File",
					filters={
						"attached_to_doctype": self.attached_to_doctype,
						"attached_to_name": self.attached_to_name,
					},
					limit=attachment_limit + 1,
				)
			)

			if current_attachment_count >= attachment_limit:
				capkpi.throw(
					_("Maximum Attachment Limit of {0} has been reached for {1} {2}.").format(
						capkpi.bold(attachment_limit), self.attached_to_doctype, self.attached_to_name
					),
					exc=capkpi.exceptions.AttachmentLimitReached,
					title=_("Attachment Limit Reached"),
				)

	def validate_remote_file(self):
		"""Validates if file uploaded using URL already exist"""
		site_url = get_url()
		if "/files/" in self.file_url and self.file_url.startswith(site_url):
			self.file_url = self.file_url.split(site_url, 1)[1]

	def set_folder_name(self):
		"""Make parent folders if not exists based on reference doctype and name"""
		if self.attached_to_doctype and not self.folder:
			self.folder = capkpi.db.get_value("File", {"is_attachments_folder": 1})

	def validate_folder(self):
		if not self.is_home_folder and not self.folder and not self.flags.ignore_folder_validate:
			self.folder = "Home"

	def validate_file(self):
		"""Validates existence of public file
		TODO: validate for private file
		"""
		full_path = self.get_full_path()

		if full_path.startswith("http"):
			return True

		if not os.path.exists(full_path):
			capkpi.throw(_("File {0} does not exist").format(self.file_url), IOError)

	def validate_duplicate_entry(self):
		if not self.flags.ignore_duplicate_entry_error and not self.is_folder:
			if not self.content_hash:
				self.generate_content_hash()

			# check duplicate name
			# check duplicate assignment
			filters = {
				"content_hash": self.content_hash,
				"is_private": self.is_private,
				"name": ("!=", self.name),
			}
			if self.attached_to_doctype and self.attached_to_name:
				filters.update(
					{"attached_to_doctype": self.attached_to_doctype, "attached_to_name": self.attached_to_name}
				)
			duplicate_file = capkpi.db.get_value("File", filters, ["name", "file_url"], as_dict=1)

			if duplicate_file:
				duplicate_file_doc = capkpi.get_cached_doc("File", duplicate_file.name)
				if duplicate_file_doc.exists_on_disk():
					# just use the url, to avoid uploading a duplicate
					self.file_url = duplicate_file.file_url

	def set_file_name(self):
		if not self.file_name and self.file_url:
			self.file_name = self.file_url.split("/")[-1]
		else:
			self.file_name = re.sub(r"/", "", self.file_name)

	def generate_content_hash(self):
		if self.content_hash or not self.file_url or self.file_url.startswith("http"):
			return
		file_name = self.file_url.split("/")[-1]
		try:
			with open(get_files_path(file_name, is_private=self.is_private), "rb") as f:
				self.content_hash = get_content_hash(f.read())
		except IOError:
			capkpi.throw(_("File {0} does not exist").format(self.file_url))

	def on_trash(self):
		if self.is_home_folder or self.is_attachments_folder:
			capkpi.throw(_("Cannot delete Home and Attachments folders"))
		self.check_folder_is_empty()
		self.call_delete_file()
		if not self.is_folder:
			self.add_comment_in_reference_doc("Attachment Removed", _("Removed {0}").format(self.file_name))

	def make_thumbnail(
		self, set_as_thumbnail=True, width=300, height=300, suffix="small", crop=False
	):
		if self.file_url:
			try:
				if self.file_url.startswith(("/files", "/private/files")):
					image, filename, extn = get_local_image(self.file_url)
				else:
					image, filename, extn = get_web_image(self.file_url)
			except (HTTPError, SSLError, IOError, TypeError):
				return

			size = width, height
			if crop:
				image = ImageOps.fit(image, size, Image.ANTIALIAS)
			else:
				image.thumbnail(size, Image.ANTIALIAS)

			thumbnail_url = filename + "_" + suffix + "." + extn
			path = os.path.abspath(capkpi.get_site_path("public", thumbnail_url.lstrip("/")))

			try:
				image.save(path)
				if set_as_thumbnail:
					self.db_set("thumbnail_url", thumbnail_url)

			except IOError:
				capkpi.msgprint(_("Unable to write file format for {0}").format(path))
				return

			return thumbnail_url

	def check_folder_is_empty(self):
		"""Throw exception if folder is not empty"""
		files = capkpi.get_all("File", filters={"folder": self.name}, fields=("name", "file_name"))

		if self.is_folder and files:
			capkpi.throw(_("Folder {0} is not empty").format(self.name), FolderNotEmpty)

	def call_delete_file(self):
		"""If file not attached to any other record, delete it"""
		if (
			self.file_name
			and self.content_hash
			and (
				not capkpi.db.count("File", {"content_hash": self.content_hash, "name": ["!=", self.name]})
			)
		):
			self.delete_file_data_content()
		elif self.file_url:
			self.delete_file_data_content(only_thumbnail=True)

	def on_rollback(self):
		self.flags.on_rollback = True
		self.on_trash()

	def unzip(self):
		"""Unzip current file and replace it by its children"""
		if not self.file_url.endswith(".zip"):
			capkpi.throw(_("{0} is not a zip file").format(self.file_name))

		zip_path = self.get_full_path()

		files = []
		with zipfile.ZipFile(zip_path) as z:
			for file in z.filelist:
				if file.is_dir() or file.filename.startswith("__MACOSX/"):
					# skip directories and macos hidden directory
					continue

				filename = os.path.basename(file.filename)
				if filename.startswith("."):
					# skip hidden files
					continue

				file_doc = capkpi.new_doc("File")
				file_doc.content = z.read(file.filename)
				file_doc.file_name = filename
				file_doc.folder = self.folder
				file_doc.is_private = self.is_private
				file_doc.attached_to_doctype = self.attached_to_doctype
				file_doc.attached_to_name = self.attached_to_name
				file_doc.save()
				files.append(file_doc)

		capkpi.delete_doc("File", self.name)
		return files

	def exists_on_disk(self):
		exists = os.path.exists(self.get_full_path())
		return exists

	def get_content(self):
		"""Returns [`file_name`, `content`] for given file name `fname`"""
		if self.is_folder:
			capkpi.throw(_("Cannot get file contents of a Folder"))

		if self.get("content"):
			return self.content

		self.validate_url()
		file_path = self.get_full_path()

		# read the file
		if PY2:
			with open(encode(file_path)) as f:
				content = f.read()
		else:
			with io.open(encode(file_path), mode="rb") as f:
				content = f.read()
				try:
					# for plain text files
					content = content.decode()
				except UnicodeDecodeError:
					# for .png, .jpg, etc
					pass

		return content

	def get_full_path(self):
		"""Returns file path from given file name"""

		file_path = self.file_url or self.file_name

		site_url = get_url()
		if "/files/" in file_path and file_path.startswith(site_url):
			file_path = file_path.split(site_url, 1)[1]

		if "/" not in file_path:
			file_path = "/files/" + file_path

		if file_path.startswith("/private/files/"):
			file_path = get_files_path(*file_path.split("/private/files/", 1)[1].split("/"), is_private=1)

		elif file_path.startswith("/files/"):
			file_path = get_files_path(*file_path.split("/files/", 1)[1].split("/"))

		elif file_path.startswith("http"):
			pass

		elif not self.file_url:
			capkpi.throw(_("There is some problem with the file url: {0}").format(file_path))

		return file_path

	def write_file(self):
		"""write file to disk with a random name (to compare)"""
		file_path = get_files_path(is_private=self.is_private)

		if os.path.sep in self.file_name:
			capkpi.throw(_("File name cannot have {0}").format(os.path.sep))

		# create directory (if not exists)
		capkpi.create_folder(file_path)
		# write the file
		self.content = self.get_content()
		if isinstance(self.content, text_type):
			self.content = self.content.encode()
		with open(os.path.join(file_path.encode("utf-8"), self.file_name.encode("utf-8")), "wb+") as f:
			f.write(self.content)

		return get_files_path(self.file_name, is_private=self.is_private)

	def save_file(self, content=None, decode=False, ignore_existing_file_check=False):
		file_exists = False
		self.content = content

		if decode:
			if isinstance(content, text_type):
				self.content = content.encode("utf-8")

			if b"," in self.content:
				self.content = self.content.split(b",")[1]
			self.content = base64.b64decode(self.content)

		if not self.is_private:
			self.is_private = 0

		self.content_type = mimetypes.guess_type(self.file_name)[0]

		self.file_size = self.check_max_file_size()

		if (
			self.content_type
			and self.content_type == "image/jpeg"
			and capkpi.get_system_settings("strip_exif_metadata_from_uploaded_images")
		):
			self.content = strip_exif_data(self.content, self.content_type)

		self.content_hash = get_content_hash(self.content)

		duplicate_file = None

		# check if a file exists with the same content hash and is also in the same folder (public or private)
		if not ignore_existing_file_check:
			duplicate_file = capkpi.get_value(
				"File",
				{"content_hash": self.content_hash, "is_private": self.is_private},
				["file_url", "name"],
				as_dict=True,
			)

		if duplicate_file:
			file_doc = capkpi.get_cached_doc("File", duplicate_file.name)
			if file_doc.exists_on_disk():
				self.file_url = duplicate_file.file_url
				file_exists = True

		if os.path.exists(encode(get_files_path(self.file_name, is_private=self.is_private))):
			self.file_name = get_file_name(self.file_name, self.content_hash[-6:])

		if not file_exists:
			call_hook_method("before_write_file", file_size=self.file_size)
			write_file_method = get_hook_method("write_file")
			if write_file_method:
				return write_file_method(self)
			return self.save_file_on_filesystem()

	def save_file_on_filesystem(self):
		fpath = self.write_file()

		if self.is_private:
			self.file_url = "/private/files/{0}".format(self.file_name)
		else:
			self.file_url = "/files/{0}".format(self.file_name)

		return {"file_name": os.path.basename(fpath), "file_url": self.file_url}

	def check_max_file_size(self):
		max_file_size = get_max_file_size()
		file_size = len(self.content)

		if file_size > max_file_size:
			capkpi.msgprint(
				_("File size exceeded the maximum allowed size of {0} MB").format(max_file_size / 1048576),
				raise_exception=MaxFileSizeReachedError,
			)

		return file_size

	def delete_file_data_content(self, only_thumbnail=False):
		method = get_hook_method("delete_file_data_content")
		if method:
			method(self, only_thumbnail=only_thumbnail)
		else:
			self.delete_file_from_filesystem(only_thumbnail=only_thumbnail)

	def delete_file_from_filesystem(self, only_thumbnail=False):
		"""Delete file, thumbnail from File document"""
		if only_thumbnail:
			delete_file(self.thumbnail_url)
		else:
			delete_file(self.file_url)
			delete_file(self.thumbnail_url)

	def is_downloadable(self):
		return has_permission(self, "read")

	def get_extension(self):
		"""returns split filename and extension"""
		return os.path.splitext(self.file_name)

	def add_comment_in_reference_doc(self, comment_type, text):
		if self.attached_to_doctype and self.attached_to_name:
			try:
				doc = capkpi.get_doc(self.attached_to_doctype, self.attached_to_name)
				doc.add_comment(comment_type, text)
			except capkpi.DoesNotExistError:
				capkpi.clear_messages()

	def set_is_private(self):
		if self.file_url:
			self.is_private = cint(self.file_url.startswith("/private"))


def on_doctype_update():
	capkpi.db.add_index("File", ["attached_to_doctype", "attached_to_name"])


def make_home_folder():
	home = capkpi.get_doc(
		{"doctype": "File", "is_folder": 1, "is_home_folder": 1, "file_name": _("Home")}
	).insert()

	capkpi.get_doc(
		{
			"doctype": "File",
			"folder": home.name,
			"is_folder": 1,
			"is_attachments_folder": 1,
			"file_name": _("Attachments"),
		}
	).insert()


@capkpi.whitelist()
def create_new_folder(file_name, folder):
	"""create new folder under current parent folder"""
	file = capkpi.new_doc("File")
	file.file_name = file_name
	file.is_folder = 1
	file.folder = folder
	file.insert(ignore_if_duplicate=True)
	return file


@capkpi.whitelist()
def move_file(file_list, new_parent, old_parent):

	if isinstance(file_list, string_types):
		file_list = json.loads(file_list)

	for file_obj in file_list:
		setup_folder_path(file_obj.get("name"), new_parent)

	# recalculate sizes
	capkpi.get_doc("File", old_parent).save()
	capkpi.get_doc("File", new_parent).save()


def setup_folder_path(filename, new_parent):
	file = capkpi.get_doc("File", filename)
	file.folder = new_parent
	file.save()

	if file.is_folder:
		from capkpi.model.rename_doc import rename_doc

		rename_doc("File", file.name, file.get_name_based_on_parent_folder(), ignore_permissions=True)


def get_extension(filename, extn, content: bytes = None, response: "Response" = None) -> str:
	mimetype = None

	if response:
		content_type = response.headers.get("Content-Type")

		if content_type:
			_extn = mimetypes.guess_extension(content_type)
			if _extn:
				return _extn[1:]

	if extn:
		# remove '?' char and parameters from extn if present
		if "?" in extn:
			extn = extn.split("?", 1)[0]

		mimetype = mimetypes.guess_type(filename + "." + extn)[0]

	if mimetype is None or not mimetype.startswith("image/") and content:
		# detect file extension by reading image header properties
		extn = imghdr.what(filename + "." + (extn or ""), h=content)

	return extn


def get_local_image(file_url):
	if file_url.startswith("/private"):
		file_url_path = (file_url.lstrip("/"),)
	else:
		file_url_path = ("public", file_url.lstrip("/"))

	file_path = capkpi.get_site_path(*file_url_path)

	try:
		image = Image.open(file_path)
	except IOError:
		capkpi.throw(_("Unable to read file format for {0}").format(file_url))

	content = None

	try:
		filename, extn = file_url.rsplit(".", 1)
	except ValueError:
		# no extn
		with open(file_path, "r") as f:
			content = f.read()

		filename = file_url
		extn = None

	extn = get_extension(filename, extn, content)

	return image, filename, extn


def get_web_image(file_url: str) -> Tuple["ImageFile", str, str]:
	# download
	file_url = capkpi.utils.get_url(file_url)
	r = requests.get(file_url, stream=True)
	try:
		r.raise_for_status()
	except HTTPError:
		if r.status_code == 404:
			capkpi.msgprint(_("File '{0}' not found").format(file_url))
		else:
			capkpi.msgprint(_("Unable to read file format for {0}").format(file_url))
		raise

	try:
		image = Image.open(BytesIO(r.content))
	except Exception as e:
		capkpi.msgprint(_("Image link '{0}' is not valid").format(file_url), raise_exception=e)

	try:
		filename, extn = file_url.rsplit("/", 1)[1].rsplit(".", 1)
	except ValueError:
		# the case when the file url doesn't have filename or extension
		# but is fetched due to a query string. example: https://encrypted-tbn3.gstatic.com/images?q=something
		filename = get_random_filename()
		extn = None

	extn = get_extension(filename, extn, response=r)
	if extn == "bin":
		extn = get_extension(filename, extn, content=r.content) or "png"

	filename = "/files/" + strip(unquote(filename))

	return image, filename, extn


def delete_file(path):
	"""Delete file from `public folder`"""
	if path:
		if ".." in path.split("/"):
			capkpi.msgprint(
				_("It is risky to delete this file: {0}. Please contact your System Manager.").format(path)
			)

		parts = os.path.split(path.strip("/"))
		if parts[0] == "files":
			path = capkpi.utils.get_site_path("public", "files", parts[-1])

		else:
			path = capkpi.utils.get_site_path("private", "files", parts[-1])

		path = encode(path)
		if os.path.exists(path):
			os.remove(path)


def get_max_file_size():
	return cint(conf.get("max_file_size")) or 10485760


def has_permission(doc, ptype=None, user=None):
	has_access = False
	user = user or capkpi.session.user

	if ptype == "create":
		has_access = capkpi.has_permission("File", "create", user=user)

	if not doc.is_private or doc.owner in [user, "Guest"] or user == "Administrator":
		has_access = True

	if doc.attached_to_doctype and doc.attached_to_name:
		attached_to_doctype = doc.attached_to_doctype
		attached_to_name = doc.attached_to_name

		try:
			ref_doc = capkpi.get_doc(attached_to_doctype, attached_to_name)

			if ptype in ["write", "create", "delete"]:
				has_access = ref_doc.has_permission("write")

				if ptype == "delete" and not has_access:
					capkpi.throw(
						_(
							"Cannot delete file as it belongs to {0} {1} for which you do not have permissions"
						).format(doc.attached_to_doctype, doc.attached_to_name),
						capkpi.PermissionError,
					)
			else:
				has_access = ref_doc.has_permission("read")
		except capkpi.DoesNotExistError:
			# if parent doc is not created before file is created
			# we cannot check its permission so we will use file's permission
			pass

	return has_access


def remove_file_by_url(file_url, doctype=None, name=None):
	if doctype and name:
		fid = capkpi.db.get_value(
			"File", {"file_url": file_url, "attached_to_doctype": doctype, "attached_to_name": name}
		)
	else:
		fid = capkpi.db.get_value("File", {"file_url": file_url})

	if fid:
		from capkpi.utils.file_manager import remove_file

		return remove_file(fid=fid)


def get_content_hash(content):
	if isinstance(content, text_type):
		content = content.encode()
	return hashlib.md5(content).hexdigest()  # nosec


def get_file_name(fname, optional_suffix):
	# convert to unicode
	fname = cstr(fname)

	f = fname.rsplit(".", 1)
	if len(f) == 1:
		partial, extn = f[0], ""
	else:
		partial, extn = f[0], "." + f[1]
	return "{partial}{suffix}{extn}".format(partial=partial, extn=extn, suffix=optional_suffix)


@capkpi.whitelist()
def download_file(file_url):
	"""
	Download file using token and REST API. Valid session or
	token is required to download private files.

	Method : GET
	Endpoint : capkpi.core.doctype.file.file.download_file
	URL Params : file_name = /path/to/file relative to site path
	"""
	file_doc = capkpi.get_doc("File", {"file_url": file_url})
	file_doc.check_permission("read")

	capkpi.local.response.filename = os.path.basename(file_url)
	capkpi.local.response.filecontent = file_doc.get_content()
	capkpi.local.response.type = "download"


def extract_images_from_doc(doc, fieldname):
	content = doc.get(fieldname)
	content = extract_images_from_html(doc, content)
	if capkpi.flags.has_dataurl:
		doc.set(fieldname, content)


def extract_images_from_html(doc, content, is_private=False):
	capkpi.flags.has_dataurl = False

	def _save_file(match):
		data = match.group(1).split("data:")[1]
		headers, content = data.split(",")

		if "filename=" in headers:
			filename = headers.split("filename=")[-1]
			filename = safe_decode(filename).split(";")[0]

			# decode filename
			if not isinstance(filename, text_type):
				filename = text_type(filename, "utf-8")
		else:
			mtype = headers.split(";")[0]
			filename = get_random_filename(content_type=mtype)

		if doc.meta.istable:
			doctype = doc.parenttype
			name = doc.parent
		else:
			doctype = doc.doctype
			name = doc.name

		_file = capkpi.get_doc(
			{
				"doctype": "File",
				"file_name": filename,
				"attached_to_doctype": doctype,
				"attached_to_name": name,
				"content": content,
				"decode": True,
				"is_private": is_private,
			}
		)
		_file.save(ignore_permissions=True)

		file_url = _file.file_url
		capkpi.flags.has_dataurl = True

		return '<img src="{file_url}"'.format(file_url=file_url)

	if content and isinstance(content, string_types):
		content = re.sub(r'<img[^>]*src\s*=\s*["\'](?=data:)(.*?)["\']', _save_file, content)

	return content


def get_random_filename(content_type=None):
	extn = None
	if content_type:
		extn = mimetypes.guess_extension(content_type)

	return random_string(7) + (extn or "")


@capkpi.whitelist()
def unzip_file(name):
	"""Unzip the given file and make file records for each of the extracted files"""
	file_obj = capkpi.get_doc("File", name)
	files = file_obj.unzip()
	return files


@capkpi.whitelist()
def get_attached_images(doctype, names):
	"""get list of image urls attached in form
	returns {name: ['image.jpg', 'image.png']}"""

	if isinstance(names, string_types):
		names = json.loads(names)

	img_urls = capkpi.db.get_list(
		"File",
		filters={"attached_to_doctype": doctype, "attached_to_name": ("in", names), "is_folder": 0},
		fields=["file_url", "attached_to_name as docname"],
	)

	out = capkpi._dict()
	for i in img_urls:
		out[i.docname] = out.get(i.docname, [])
		out[i.docname].append(i.file_url)

	return out


@capkpi.whitelist()
def get_files_in_folder(folder, start=0, page_length=20):
	start = cint(start)
	page_length = cint(page_length)

	attachment_folder = capkpi.db.get_value(
		"File", "Home/Attachments", ["name", "file_name", "file_url", "is_folder", "modified"], as_dict=1
	)

	files = capkpi.db.get_list(
		"File",
		{"folder": folder},
		["name", "file_name", "file_url", "is_folder", "modified"],
		start=start,
		page_length=page_length + 1,
	)

	if folder == "Home" and attachment_folder not in files:
		files.insert(0, attachment_folder)

	return {"files": files[:page_length], "has_more": len(files) > page_length}


@capkpi.whitelist()
def get_files_by_search_text(text):
	if not text:
		return []

	text = "%" + cstr(text).lower() + "%"
	return capkpi.db.get_all(
		"File",
		fields=["name", "file_name", "file_url", "is_folder", "modified"],
		filters={"is_folder": False},
		or_filters={"file_name": ("like", text), "file_url": text, "name": ("like", text)},
		order_by="modified desc",
		limit=20,
	)


def update_existing_file_docs(doc):
	# Update is private and file url of all file docs that point to the same file
	capkpi.db.sql(
		"""
		UPDATE `tabFile`
		SET
			file_url = %(file_url)s,
			is_private = %(is_private)s
		WHERE
			content_hash = %(content_hash)s
			and name != %(file_name)s
	""",
		dict(
			file_url=doc.file_url,
			is_private=doc.is_private,
			content_hash=doc.content_hash,
			file_name=doc.name,
		),
	)


def attach_files_to_document(doc, event):
	"""Runs on on_update hook of all documents.
	Goes through every Attach and Attach Image field and attaches
	the file url to the document if it is not already attached.
	"""

	attach_fields = doc.meta.get("fields", {"fieldtype": ["in", ["Attach", "Attach Image"]]})

	for df in attach_fields:
		# this method runs in on_update hook of all documents
		# we dont want the update to fail if file cannot be attached for some reason
		try:
			value = doc.get(df.fieldname)
			if not (value or "").startswith(("/files", "/private/files")):
				return

			if capkpi.db.exists(
				"File",
				{
					"file_url": value,
					"attached_to_name": doc.name,
					"attached_to_doctype": doc.doctype,
					"attached_to_field": df.fieldname,
				},
			):
				return

			capkpi.get_doc(
				doctype="File",
				file_url=value,
				attached_to_name=doc.name,
				attached_to_doctype=doc.doctype,
				attached_to_field=df.fieldname,
				folder="Home/Attachments",
			).insert(ignore_permissions=True)
		except Exception:
			capkpi.log_error(title=_("Error Attaching File"))