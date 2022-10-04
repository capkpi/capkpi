const path = require('path');

function scrub_html_template(content) {
	content = content.replace(/\s/g, ' ');
	content = content.replace(/(<!--.*?-->)/g, '');
	return content.replace("'", "\'"); // eslint-disable-line
}

module.exports = function capkpi_html() {
	return {
		name: 'capkpi-html',
		transform(code, id) {
			if (!id.endsWith('.html')) return null;

			var filepath = path.basename(id).split('.');
			filepath.splice(-1);

			var key = filepath.join(".");
			var content = scrub_html_template(code);

			return `
				capkpi.templates['${key}'] = '${content}';
			`;
		}
	};
};
