// Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

capkpi.provide('capkpi.meta.docfield_map');
capkpi.provide('capkpi.meta.docfield_copy');
capkpi.provide('capkpi.meta.docfield_list');
capkpi.provide('capkpi.meta.doctypes');
capkpi.provide("capkpi.meta.precision_map");

capkpi.get_meta = function(doctype) {
	return locals['DocType'] ? locals['DocType'][doctype] : null;
}

$.extend(capkpi.meta, {
	sync: function(doc) {
		$.each(doc.fields, function(i, df) {
			capkpi.meta.add_field(df);
		})
		capkpi.meta.sync_messages(doc);
		if(doc.__print_formats) capkpi.model.sync(doc.__print_formats);
		if(doc.__workflow_docs) capkpi.model.sync(doc.__workflow_docs);
	},

	// build docfield_map and docfield_list
	add_field: function(df) {
		capkpi.provide('capkpi.meta.docfield_map.' + df.parent);
		capkpi.meta.docfield_map[df.parent][df.fieldname || df.label] = df;

		if(!capkpi.meta.docfield_list[df.parent])
			capkpi.meta.docfield_list[df.parent] = [];

		// check for repeat
		for(var i in capkpi.meta.docfield_list[df.parent]) {
			var d = capkpi.meta.docfield_list[df.parent][i];
			if(df.fieldname==d.fieldname)
				return; // no repeat
		}
		capkpi.meta.docfield_list[df.parent].push(df);
	},

	make_docfield_copy_for: function(doctype, docname, docfield_list=null) {
		var c = capkpi.meta.docfield_copy;
		if(!c[doctype])
			c[doctype] = {};
		if(!c[doctype][docname])
			c[doctype][docname] = {};

		docfield_list = docfield_list || capkpi.meta.docfield_list[doctype] || [];
		for(var i=0, j=docfield_list.length; i<j; i++) {
			var df = docfield_list[i];
			c[doctype][docname][df.fieldname || df.label] = copy_dict(df);
		}
	},

	get_field: function(doctype, fieldname, name) {
		var out = capkpi.meta.get_docfield(doctype, fieldname, name);

		// search in standard fields
		if (!out) {
			capkpi.model.std_fields.every(function(d) {
				if(d.fieldname===fieldname) {
					out = d;
					return false;
				} else {
					return true;
				}
			});
		}
		return out;
	},

	get_docfield: function(doctype, fieldname, name) {
		var fields_dict = capkpi.meta.get_docfield_copy(doctype, name);
		return fields_dict ? fields_dict[fieldname] : null;
	},

	set_formatter: function(doctype, fieldname, name, formatter) {
		capkpi.meta.get_docfield(doctype, fieldname, name).formatter = formatter;
	},

	set_indicator_formatter: function(doctype, fieldname, name, get_text, get_color) {
		capkpi.meta.get_docfield(doctype, fieldname, name).formatter =
			function(value, df, options, doc) {
				return repl('<span class="indicator %(color)s">%(name)s</span>', {
					color: get_color(),
					name: get_text()
				});
			};
	},

	get_docfields: function(doctype, name, filters) {
		var docfield_map = capkpi.meta.get_docfield_copy(doctype, name);

		var docfields = capkpi.meta.sort_docfields(docfield_map);

		if(filters) {
			docfields = capkpi.utils.filter_dict(docfields, filters);
		}

		return docfields;
	},

	get_linked_fields: function(doctype) {
		return $.map(capkpi.get_meta(doctype).fields,
			function(d) { return d.fieldtype=="Link" ? d.options : null; });
	},

	get_fields_to_check_permissions: function(doctype) {
		var fields = $.map(capkpi.meta.get_docfields(doctype, name), function(df) {
			return (df.fieldtype==="Link" && df.ignore_user_permissions!==1) ? df : null;
		});
		fields = fields.concat({label: "Name", fieldname: name, options: doctype});
		return fields;
	},

	sort_docfields: function(docs) {
		return $.map(docs, function(d) { return d; }).sort(function(a, b) { return a.idx - b.idx });
	},

	get_docfield_copy: function(doctype, name) {
		if(!name) return capkpi.meta.docfield_map[doctype];

		if(!(capkpi.meta.docfield_copy[doctype] && capkpi.meta.docfield_copy[doctype][name])) {
			capkpi.meta.make_docfield_copy_for(doctype, name);
		}

		return capkpi.meta.docfield_copy[doctype][name];
	},

	get_fieldnames: function(doctype, name, filters) {
		return $.map(capkpi.utils.filter_dict(capkpi.meta.docfield_map[doctype], filters),
			function(df) { return df.fieldname; });
	},

	has_field: function(dt, fn) {
		let docfield_map = capkpi.meta.docfield_map[dt];
		return docfield_map && docfield_map[fn];
	},

	get_table_fields: function(dt) {
		return $.map(capkpi.meta.docfield_list[dt], function(d) {
			return capkpi.model.table_fields.includes(d.fieldtype) ? d : null});
	},

	get_doctype_for_field: function(doctype, key) {
		var out = null;
		if(in_list(capkpi.model.std_fields_list, key)) {
			// standard
			out = doctype;
		} else if(capkpi.meta.has_field(doctype, key)) {
			// found in parent
			out = doctype;
		} else {
			capkpi.meta.get_table_fields(doctype).every(function(d) {
				if(capkpi.meta.has_field(d.options, key)) {
					out = d.options;
					return false;
				}
				return true;
			});

			if(!out) {
				// eslint-disable-next-line
				console.log(__('Warning: Unable to find {0} in any table related to {1}', [key, __(doctype)]));
			}
		}
		return out;
	},

	get_parentfield: function(parent_dt, child_dt) {
		var df = (capkpi.get_doc("DocType", parent_dt).fields || [])
			.filter(df => capkpi.model.table_fields.includes(df.fieldtype) && df.options===child_dt)
		if(!df.length)
			throw "parentfield not found for " + parent_dt + ", " + child_dt;
		return df[0].fieldname;
	},

	get_label: function(dt, fn, dn) {
		var standard = {
			'owner': __('Owner'),
			'creation': __('Created On'),
			'modified': __('Last Modified On'),
			'idx': __('Idx'),
			'name': __('Name'),
			'modified_by': __('Last Modified By')
		}
		if(standard[fn]) {
			return standard[fn];
		} else {
			var df = this.get_docfield(dt, fn, dn);
			return (df ? df.label : "") || fn;
		}
	},

	get_print_sizes: function() {
		return [
			"A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9",
			"B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10",
			"C5E", "Comm10E", "DLE", "Executive", "Folio", "Ledger", "Legal",
			"Letter", "Tabloid", "Custom"
		];
	},

	get_print_formats: function(doctype) {
		var print_format_list = ["Standard"];
		var default_print_format = locals.DocType[doctype].default_print_format;
		let enable_raw_printing = capkpi.model.get_doc(":Print Settings", "Print Settings").enable_raw_printing;
		var print_formats = capkpi.get_list("Print Format", {doc_type: doctype})
			.sort(function(a, b) { return (a > b) ? 1 : -1; });
		$.each(print_formats, function(i, d) {
			if (
				!in_list(print_format_list, d.name)
				&& d.print_format_type !== 'JS'
				&& (cint(enable_raw_printing) || !d.raw_printing)
			) {
				print_format_list.push(d.name);
			}
		});

		if(default_print_format && default_print_format != "Standard") {
			var index = print_format_list.indexOf(default_print_format);
			print_format_list.splice(index, 1).sort();
			print_format_list.unshift(default_print_format);
		}

		return print_format_list;
	},

	sync_messages: function(doc) {
		if(doc.__messages) {
			$.extend(capkpi._messages, doc.__messages);
		}
	},

	get_field_currency: function(df, doc) {
		var currency = capkpi.boot.sysdefaults.currency;
		if(!doc && cur_frm)
			doc = cur_frm.doc;

		if(df && df.options) {
			if(doc && df.options.indexOf(":")!=-1) {
				var options = df.options.split(":");
				if(options.length==3) {
					// get reference record e.g. Company
					var docname = doc[options[1]];
					if(!docname && cur_frm) {
						docname = cur_frm.doc[options[1]];
					}
					currency = capkpi.model.get_value(options[0], docname, options[2]) ||
						capkpi.model.get_value(":" + options[0], docname, options[2]) ||
						currency;
				}
			} else if(doc && doc[df.options]) {
				currency = doc[df.options];
			} else if(cur_frm && cur_frm.doc[df.options]) {
				currency = cur_frm.doc[df.options];
			}
		}
		return currency;
	},

	get_field_precision: function(df, doc) {
		var precision = null;
		if (df && df.precision) {
			precision = cint(df.precision);
		} else if(df && df.fieldtype === "Currency") {
			precision = cint(capkpi.defaults.get_default("currency_precision"));
			if(!precision) {
				var number_format = get_number_format();
				var number_format_info = get_number_format_info(number_format);
				precision = number_format_info.precision;
			}
		} else {
			precision = cint(capkpi.defaults.get_default("float_precision")) || 3;
		}
		return precision;
	}
});
