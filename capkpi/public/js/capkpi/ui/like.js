// Copyright (c) 2015, CapKPI Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

capkpi.ui.is_liked = function(doc) {
	var liked = capkpi.ui.get_liked_by(doc);
	return liked.indexOf(capkpi.session.user)===-1 ? false : true;
}

capkpi.ui.get_liked_by = function(doc) {
	var liked = doc._liked_by;
	if(liked) {
		liked = JSON.parse(liked);
	}

	return liked || [];
}

capkpi.ui.toggle_like = function($btn, doctype, name, callback) {
	var add = $btn.hasClass("not-liked") ? "Yes" : "No";
	// disable click
	$btn.css('pointer-events', 'none');

	capkpi.call({
		method: "capkpi.desk.like.toggle_like",
		quiet: true,
		args: {
			doctype: doctype,
			name: name,
			add: add,
		},
		callback: function(r) {
			// renable click
			$btn.css('pointer-events', 'auto');

			if(!r.exc) {
				// update in all local-buttons
				var action_buttons = $('.like-action[data-name="'+ name.replace(/"/g, '\"')
					+'"][data-doctype="'+ doctype.replace(/"/g, '\"')+'"]');

				if(add==="Yes") {
					action_buttons.removeClass("not-liked").addClass("liked");
				} else {
					action_buttons.addClass("not-liked").removeClass("liked");
				}

				// update in locals (form)
				var doc = locals[doctype] && locals[doctype][name];
				if(doc) {
					var liked_by = JSON.parse(doc._liked_by || "[]"),
						idx = liked_by.indexOf(capkpi.session.user);
					if(add==="Yes") {
						if(idx===-1)
							liked_by.push(capkpi.session.user);
					} else {
						if(idx!==-1) {
							liked_by = liked_by.slice(0,idx).concat(liked_by.slice(idx+1))
						}
					}
					doc._liked_by = JSON.stringify(liked_by);
				}

				if(callback) {
					callback();
				}
			}
		}
	});
};

capkpi.ui.click_toggle_like = function() {
	var $btn = $(this);
	var $count = $btn.siblings(".likes-count");
	var not_liked = $btn.hasClass("not-liked");
	var doctype = $btn.attr("data-doctype");
	var name = $btn.attr("data-name");

	capkpi.ui.toggle_like($btn, doctype, name, function() {
		if (not_liked) {
			$count.text(cint($count.text()) + 1);
		} else {
			$count.text(cint($count.text()) - 1);
		}
	});

	return false;
}

capkpi.ui.setup_like_popover = ($parent, selector, check_not_liked=true) => {
	if (capkpi.dom.is_touchscreen()) {
		return;
	}

	$parent.on('mouseover', selector, function() {
		const target_element = $(this);
		target_element.popover({
			animation: true,
			placement: 'bottom',
			trigger: 'manual',
			template: `<div class="liked-by-popover popover">
				<div class="arrow"></div>
				<div class="popover-body popover-content"></div>
			</div>`,
			content: () => {
				let liked_by = target_element.parents(".liked-by").attr('data-liked-by');
				liked_by = liked_by ? decodeURI(liked_by) : '[]';
				liked_by = JSON.parse(liked_by);

				const user = capkpi.session.user;
				// hack
				if (check_not_liked) {
					if (target_element.parents(".liked-by").find(".not-liked").length) {
						if (liked_by.indexOf(user)!==-1) {
							liked_by.splice(liked_by.indexOf(user), 1);
						}
					} else {
						if (liked_by.indexOf(user)===-1) {
							liked_by.push(user);
						}
					}
				}

				if (!liked_by.length) {
					return "";
				}

				let liked_by_list = $(`<ul class="list-unstyled"></ul>`);

				// to show social profile of the user
				let link_base = '/app/user-profile/';

				liked_by.forEach(user => {
					// append user list item
					liked_by_list.append(`
						<li data-user=${user}>${capkpi.avatar(user, "avatar-xs")}
							<span>${capkpi.user.full_name(user)}</span>
						</li>
					`);
				});

				liked_by_list.children('li').click(ev => {
					let user = ev.currentTarget.dataset.user;
					target_element.popover('hide');
					capkpi.set_route(link_base + user);
				});

				return liked_by_list;
			},
			html: true,
			container: 'body'
		});

		target_element.popover('show');

		$(".popover").on("mouseleave", () => {
			target_element.popover('hide');
		});

		target_element.on('mouseout', () => {
			setTimeout(() => {
				if (!$('.popover:hover').length) {
					target_element.popover('hide');
				}
			}, 100);
		});
	});

};