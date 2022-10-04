# Copyright (c) 2021, FOSS United and contributors
# For license information, please see license.txt

import capkpi
from capkpi.model.document import Document


class DiscussionReply(Document):
	def after_insert(self):

		replies = capkpi.db.count("Discussion Reply", {"topic": self.topic})
		template = capkpi.render_template(
			"capkpi/templates/discussions/reply_card.html",
			{"reply": self, "topic": {"name": self.topic}, "loop": {"index": replies}},
		)

		topic_info = capkpi.get_all(
			"Discussion Topic",
			{"name": self.topic},
			["reference_doctype", "reference_docname", "name", "title", "owner", "creation"],
		)

		sidebar = capkpi.render_template(
			"capkpi/templates/discussions/sidebar.html", {"topic": topic_info[0]}
		)

		new_topic_template = capkpi.render_template(
			"capkpi/templates/discussions/reply_section.html", {"topics": topic_info}
		)

		capkpi.publish_realtime(
			event="publish_message",
			message={
				"template": template,
				"topic_info": topic_info[0],
				"sidebar": sidebar,
				"new_topic_template": new_topic_template,
			},
			after_commit=True,
		)
