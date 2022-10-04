// Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

capkpi.provide('capkpi.views.formview');

capkpi.views.FormFactory = class FormFactory extends capkpi.views.Factory {
	make(route) {
		var doctype = route[1],
			doctype_layout = capkpi.router.doctype_layout || doctype;

		if (!capkpi.views.formview[doctype_layout]) {
			capkpi.model.with_doctype(doctype, () => {
				this.page = capkpi.container.add_page(doctype_layout);
				capkpi.views.formview[doctype_layout] = this.page;
				this.make_and_show(doctype, route);
			});
		} else {
			this.show_doc(route);
		}

		this.setup_events();
	}

	make_and_show(doctype, route) {
		if (capkpi.router.doctype_layout) {
			capkpi.model.with_doc('DocType Layout', capkpi.router.doctype_layout, () => {
				this.make_form(doctype);
				this.show_doc(route);
			});
		} else {
			this.make_form(doctype);
			this.show_doc(route);
		}
	}

	make_form(doctype) {
		this.page.frm = new capkpi.ui.form.Form(doctype, this.page, true, capkpi.router.doctype_layout);
	}

	setup_events() {
		if (!this.initialized) {
			$(document).on("page-change", function() {
				capkpi.ui.form.close_grid_form();
			});

			capkpi.realtime.on("doc_viewers", function(data) {
				// set users that currently viewing the form
				capkpi.ui.form.FormViewers.set_users(data, 'viewers');
			});

			capkpi.realtime.on("doc_typers", function(data) {
				// set users that currently typing on the form
				capkpi.ui.form.FormViewers.set_users(data, 'typers');
			});
		}
		this.initialized = true;
	}

	show_doc(route) {
		var doctype = route[1],
			doctype_layout = capkpi.router.doctype_layout || doctype,
			name = route.slice(2).join("/");

		if (capkpi.model.new_names[name]) {
			// document has been renamed, reroute
			name = capkpi.model.new_names[name];
			capkpi.set_route("Form", doctype_layout, name);
			return;
		}

		const doc = capkpi.get_doc(doctype, name);
		if (doc && capkpi.model.get_docinfo(doctype, name) && (doc.__islocal || capkpi.model.is_fresh(doc))) {
			// is document available and recent?
			this.render(doctype_layout, name);
		} else {
			this.fetch_and_render(doctype, name, doctype_layout);
		}
	}

	fetch_and_render(doctype, name, doctype_layout) {
		capkpi.model.with_doc(doctype, name, (name, r) => {
			if (r && r['403']) return; // not permitted

			if (!(locals[doctype] && locals[doctype][name])) {
				if (name && name.substr(0, 3) === 'new') {
					this.render_new_doc(doctype, name, doctype_layout);
				} else {
					capkpi.show_not_found();
				}
				return;
			}
			this.render(doctype_layout, name);
		});
	}

	render_new_doc(doctype, name, doctype_layout) {
		const new_name = capkpi.model.make_new_doc_and_get_name(doctype, true);
		if (new_name===name) {
			this.render(doctype_layout, name);
		} else {
			capkpi.route_flags.replace_route = true;
			capkpi.set_route("Form", doctype_layout, new_name);
		}
	}

	render(doctype_layout, name) {
		capkpi.container.change_to(doctype_layout);
		capkpi.views.formview[doctype_layout].frm.refresh(name);
	}
}
