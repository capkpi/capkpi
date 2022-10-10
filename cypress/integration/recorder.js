context('Recorder', () => {
	before(() => {
		cy.login();
	});

	beforeEach(() => {
		cy.visit('/app/recorder');
		return cy.window().its('capkpi').then(capkpi => {
			// reset recorder
			return capkpi.xcall("capkpi.recorder.stop").then(() => {
				return capkpi.xcall("capkpi.recorder.delete");
			});
		});
	});

	it('Recorder Empty State', () => {
		cy.get('.page-head').findByTitle('Recorder').should('exist');

		cy.get('.indicator-pill').should('contain', 'Inactive').should('have.class', 'red');

		cy.get('.page-actions').findByRole('button', {name: 'Start'}).should('exist');
		cy.get('.page-actions').findByRole('button', {name: 'Clear'}).should('exist');

		cy.get('.msg-box').should('contain', 'Recorder is Inactive');
		cy.get('.msg-box').findByRole('button', {name: 'Start Recording'}).should('exist');
	});

	it('Recorder Start', () => {
		cy.get('.page-actions').findByRole('button', {name: 'Start'}).click();
		cy.get('.indicator-pill').should('contain', 'Active').should('have.class', 'green');

		cy.get('.msg-box').should('contain', 'No Requests found');

		cy.visit('/app/List/DocType/List');
		cy.intercept('POST', '/api/method/capkpi.desk.reportview.get').as('list_refresh');
		cy.wait('@list_refresh');

		cy.get('.page-head').findByTitle('DocType').should('exist');
		cy.get('.list-count').should('contain', '20 of ');

		cy.visit('/app/recorder');
		cy.get('.page-head').findByTitle('Recorder').should('exist');
		cy.get('.capkpi-list .result-list').should('contain', '/api/method/capkpi.desk.reportview.get');
	});

	it('Recorder View Request', () => {
		cy.get('.page-actions').findByRole('button', {name: 'Start'}).click();

		cy.visit('/app/List/DocType/List');
		cy.intercept('POST', '/api/method/capkpi.desk.reportview.get').as('list_refresh');
		cy.wait('@list_refresh');

		cy.get('.page-head').findByTitle('DocType').should('exist');
		cy.get('.list-count').should('contain', '20 of ');

		cy.visit('/app/recorder');

		cy.get('.capkpi-list .list-row-container span')
			.contains('/api/method/capkpi')
			.should('be.visible')
			.click({force: true});

		cy.url().should('include', '/recorder/request');
		cy.get('form').should('contain', '/api/method/capkpi');
	});
});
