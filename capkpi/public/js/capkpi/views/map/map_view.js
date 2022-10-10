/**
 * capkpi.views.MapView
 */
capkpi.provide('capkpi.utils.utils');
capkpi.provide("capkpi.views");

capkpi.views.MapView = class MapView extends capkpi.views.ListView {
	get view_name() {
		return 'Map';
	}

	setup_defaults() {
		super.setup_defaults();
		this.page_title = __('{0} Map', [this.page_title]);
	}

	setup_view() {
	}

	on_filter_change() {
		this.get_coords();
	}

	render() {
		this.get_coords()
			.then(() => {
				this.render_map_view();
			});
		this.$paging_area.find('.level-left').append('<div></div>');
	}

	render_map_view() {
		this.map_id = capkpi.dom.get_unique_id();

		this.$result.html(`<div id="${this.map_id}" class="map-view-container"></div>`);

		L.Icon.Default.imagePath = '/assets/capkpi/images/leaflet/';
		this.map = L.map(this.map_id).setView(capkpi.utils.map_defaults.center,
			capkpi.utils.map_defaults.zoom);

		L.tileLayer(capkpi.utils.map_defaults.tiles,
			capkpi.utils.map_defaults.options).addTo(this.map);

		L.control.scale().addTo(this.map);
		if (this.coords.features && this.coords.features.length) {
			this.coords.features.forEach(
				coords => L.geoJSON(coords).bindPopup(coords.properties.name).addTo(this.map)
			);
			let lastCoords = this.coords.features[0].geometry.coordinates.reverse();
			this.map.panTo(lastCoords, 8);
		}
	}

	get_coords() {
		let get_coords_method = this.settings && this.settings.get_coords_method || 'capkpi.geo.utils.get_coords';

		if (cur_list.meta.fields.find(i => i.fieldname === 'location' && i.fieldtype === 'Geolocation')) {
			this.type = 'location_field';
		} else if  (cur_list.meta.fields.find(i => i.fieldname === "latitude") &&
			cur_list.meta.fields.find(i => i.fieldname === "longitude")) {
			this.type = 'coordinates';
		}
		return capkpi.call({
			method: get_coords_method,
			args: {
				doctype: this.doctype,
				filters: cur_list.filter_area.get(),
				type: this.type
			}
		}).then(r => {
			this.coords = r.message;

		});
	}


	get required_libs() {
		return [
			"assets/capkpi/js/lib/leaflet/leaflet.css",
			"assets/capkpi/js/lib/leaflet/leaflet.js"
		];
	}


};