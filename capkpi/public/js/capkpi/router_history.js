capkpi.route_history_queue = [];
const routes_to_skip = ['Form', 'social', 'setup-wizard', 'recorder'];

const save_routes = capkpi.utils.debounce(() => {
	if (capkpi.session.user === 'Guest') return;
	const routes = capkpi.route_history_queue;
	if (!routes.length) return;

	capkpi.route_history_queue = [];

	capkpi.xcall('capkpi.desk.doctype.route_history.route_history.deferred_insert', {
		'routes': routes
	}).catch(() => {
		capkpi.route_history_queue.concat(routes);
	});

}, 10000);

capkpi.router.on('change', () => {
	const route = capkpi.get_route();
	if (is_route_useful(route)) {
		capkpi.route_history_queue.push({
			'creation': capkpi.datetime.now_datetime(),
			'route': capkpi.get_route_str()
		});

		save_routes();
	}
});

function is_route_useful(route) {
	if (!route[1]) {
		return false;
	} else if ((route[0] === 'List' && !route[2]) || routes_to_skip.includes(route[0])) {
		return false;
	} else {
		return true;
	}
}