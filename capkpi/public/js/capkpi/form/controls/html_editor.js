capkpi.ui.form.ControlHTMLEditor = capkpi.ui.form.ControlMarkdownEditor.extend({
	editor_class: 'html',
	set_language() {
		this.df.options = 'HTML';
		this._super();
	},
	update_preview() {
		if (!this.markdown_preview) return;
		let value = this.get_value() || '';
		value = capkpi.dom.remove_script_and_style(value);
		this.markdown_preview.html(value);
	}
});
