capkpi.provide('capkpi.model');
capkpi.provide('capkpi.utils');

/**
 * Opens the Website Meta Tag form if it exists for {route}
 * or creates a new doc and opens the form
 */
capkpi.utils.set_meta_tag = function(route) {
	capkpi.db.exists('Website Route Meta', route)
		.then(exists => {
			if (exists) {
				capkpi.set_route('Form', 'Website Route Meta', route);
			} else {
				// new doc
				const doc = capkpi.model.get_new_doc('Website Route Meta');
				doc.__newname = route;
				capkpi.set_route('Form', doc.doctype, doc.name);
			}
		});
};
