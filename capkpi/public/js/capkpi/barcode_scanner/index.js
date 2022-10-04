capkpi.provide('capkpi.barcode');

capkpi.barcode.scan_barcode = function() {
	return new Promise((resolve, reject) => {
		if (
			window.cordova &&
			window.cordova.plugins &&
			window.cordova.plugins.barcodeScanner
		) {
			window.cordova.plugins.barcodeScanner.scan(result => {
				if (!result.cancelled) {
					resolve(result.text);
				}
			}, reject);
		} else {
			capkpi.require('/assets/js/barcode_scanner.min.js', () => {
				capkpi.barcode.get_barcode().then(barcode => {
					resolve(barcode);
				});
			});
		}
	});
};
