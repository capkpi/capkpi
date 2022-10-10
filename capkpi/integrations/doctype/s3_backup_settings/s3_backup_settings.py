# -*- coding: utf-8 -*-
# Copyright (c) 2017, CapKPI Technologies and contributors
# For license information, please see license.txt

from __future__ import print_function, unicode_literals

import os
import os.path

import boto3
from botocore.exceptions import ClientError
from rq.timeouts import JobTimeoutException

import capkpi
from capkpi import _
from capkpi.integrations.offsite_backup_utils import (
	generate_files_backup,
	get_latest_backup_file,
	send_email,
	validate_file_size,
)
from capkpi.model.document import Document
from capkpi.utils import cint
from capkpi.utils.background_jobs import enqueue


class S3BackupSettings(Document):
	def validate(self):
		if not self.enabled:
			return

		if not self.endpoint_url:
			self.endpoint_url = "https://s3.amazonaws.com"

		conn = boto3.client(
			"s3",
			aws_access_key_id=self.access_key_id,
			aws_secret_access_key=self.get_password("secret_access_key"),
			endpoint_url=self.endpoint_url,
		)

		try:
			# Head_bucket returns a 200 OK if the bucket exists and have access to it.
			# Requires ListBucket permission
			conn.head_bucket(Bucket=self.bucket)
		except ClientError as e:
			error_code = e.response["Error"]["Code"]
			bucket_name = capkpi.bold(self.bucket)
			if error_code == "403":
				msg = _("Do not have permission to access bucket {0}.").format(bucket_name)
			elif error_code == "404":
				msg = _("Bucket {0} not found.").format(bucket_name)
			else:
				msg = e.args[0]

			capkpi.throw(msg)


@capkpi.whitelist()
def take_backup():
	"""Enqueue longjob for taking backup to s3"""
	enqueue(
		"capkpi.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_s3",
		queue="long",
		timeout=1500,
	)
	capkpi.msgprint(_("Queued for backup. It may take a few minutes to an hour."))


def take_backups_daily():
	take_backups_if("Daily")


def take_backups_weekly():
	take_backups_if("Weekly")


def take_backups_monthly():
	take_backups_if("Monthly")


def take_backups_if(freq):
	if cint(capkpi.db.get_value("S3 Backup Settings", None, "enabled")):
		if capkpi.db.get_value("S3 Backup Settings", None, "frequency") == freq:
			take_backups_s3()


@capkpi.whitelist()
def take_backups_s3(retry_count=0):
	try:
		validate_file_size()
		backup_to_s3()
		send_email(True, "Amazon S3", "S3 Backup Settings", "notify_email")
	except JobTimeoutException:
		if retry_count < 2:
			args = {"retry_count": retry_count + 1}
			enqueue(
				"capkpi.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_s3",
				queue="long",
				timeout=1500,
				**args
			)
		else:
			notify()
	except Exception:
		notify()


def notify():
	error_message = capkpi.get_traceback()
	send_email(False, "Amazon S3", "S3 Backup Settings", "notify_email", error_message)


def backup_to_s3():
	from capkpi.utils import get_backups_path
	from capkpi.utils.backups import new_backup

	doc = capkpi.get_single("S3 Backup Settings")
	bucket = doc.bucket
	backup_files = cint(doc.backup_files)

	conn = boto3.client(
		"s3",
		aws_access_key_id=doc.access_key_id,
		aws_secret_access_key=doc.get_password("secret_access_key"),
		endpoint_url=doc.endpoint_url or "https://s3.amazonaws.com",
	)

	if capkpi.flags.create_new_backup:
		backup = new_backup(
			ignore_files=False,
			backup_path_db=None,
			backup_path_files=None,
			backup_path_private_files=None,
			force=True,
		)
		db_filename = os.path.join(get_backups_path(), os.path.basename(backup.backup_path_db))
		site_config = os.path.join(get_backups_path(), os.path.basename(backup.backup_path_conf))
		if backup_files:
			files_filename = os.path.join(get_backups_path(), os.path.basename(backup.backup_path_files))
			private_files = os.path.join(
				get_backups_path(), os.path.basename(backup.backup_path_private_files)
			)
	else:
		if backup_files:
			db_filename, site_config, files_filename, private_files = get_latest_backup_file(
				with_files=backup_files
			)

			if not files_filename or not private_files:
				generate_files_backup()
				db_filename, site_config, files_filename, private_files = get_latest_backup_file(
					with_files=backup_files
				)

		else:
			db_filename, site_config = get_latest_backup_file()

	folder = os.path.basename(db_filename)[:15] + "/"
	# for adding datetime to folder name

	upload_file_to_s3(db_filename, folder, conn, bucket)
	upload_file_to_s3(site_config, folder, conn, bucket)

	if backup_files:
		if private_files:
			upload_file_to_s3(private_files, folder, conn, bucket)

		if files_filename:
			upload_file_to_s3(files_filename, folder, conn, bucket)


def upload_file_to_s3(filename, folder, conn, bucket):
	destpath = os.path.join(folder, os.path.basename(filename))
	try:
		print("Uploading file:", filename)
		conn.upload_file(filename, bucket, destpath)  # Requires PutObject permission

	except Exception as e:
		capkpi.log_error()
		print("Error uploading: %s" % (e))
