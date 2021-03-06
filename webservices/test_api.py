import json
import unittest

from .tests.common import ApiBaseTest


class OverallTest(ApiBaseTest):
    # Candidate
    def test_header_info(self):
        response = self._response('/candidates')
        self.assertIn('api_version', response)
        self.assertIn('pagination', response)

    def _results(self, qry):
        response = self._response(qry)
        return response['results']

    def test_full_text_search(self):
        # changed from 'james' to 'arnold' because 'james' falls victim to stemming, and some results return 'jame' causing the assert to fail
        results = self._results('/candidates?q=arnold')
        for r in results:
            #txt = json.dumps(r).lower()
            self.assertIn('arnold', r['name'].lower())

    def test_full_text_search_with_whitespace(self):
        results = self._results('/candidates?q=barack obama')
        for r in results:
            txt = json.dumps(r).lower()
            self.assertIn('obama', txt)

    def test_full_text_no_results(self):
        results = self._results('/candidates?q=asdlkflasjdflkjasdl;kfj')
        self.assertEquals(results, [])

    def test_year_filter(self):
        results = self._results('/candidates?year=1988')
        for r in results:
            self.assertIn(1988, r['election_years'])

    def test_per_page_defaults_to_20(self):
        results = self._results('/candidates')
        self.assertEquals(len(results), 20)

    def test_per_page_param(self):
        results = self._results('/candidates?per_page=5')
        self.assertEquals(len(results), 5)

    def test_invalid_per_page_param(self):
        response = self.app.get('/candidates?per_page=-10')
        self.assertEquals(response.status_code, 400)
        response = self.app.get('/candidates?per_page=34.2')
        self.assertEquals(response.status_code, 400)
        response = self.app.get('/candidates?per_page=dynamic-wombats')
        self.assertEquals(response.status_code, 400)

    def test_page_param(self):
        page_one_and_two = self._results('/candidates?per_page=10&page=1')
        page_two = self._results('/candidates?per_page=5&page=2')
        self.assertEqual(page_two[0], page_one_and_two[5])
        for itm in page_two:
            self.assertIn(itm, page_one_and_two)


    @unittest.skip("We are just showing one year at a time, this would be a good feature for /candidate/<id> but it is not a priority right now")
    def test_multi_year(self):
        # testing search
        response = self._results('/candidate?candidate_id=P80003338&year=2012,2008')
        # search listing should aggregate years
        self.assertIn('2008, 2012', response)
        # testing single resource
        response = self._results('/candidate/P80003338?year=2012,2008')
        elections = response[0]['elections']
        self.assertEquals(len(elections), 2)

    @unittest.skip("We are just showing one year at a time, this would be a good feature for /candidate/<id> but it is not a priority right now")
    def test_multi_year(self):
        # testing search
        response = self._results('/candidates?candidate_id=P80003338&year=2012,2008')
        # search listing should aggregate years
        self.assertIn('2008, 2012', response)
        # testing single resource
        response = self._results('/candidate/P80003338?year=2012,2008')
        elections = response[0]['elections']
        self.assertEquals(len(elections), 2)

    def test_cand_filters(self):
        # checking one example from each field
        orig_response = self._response('/candidates')
        original_count = orig_response['pagination']['count']

        filter_fields = (
            ('office','H'),
            ('district', '00,02'),
            ('state', 'CA'),
            ('name', 'Obama'),
            ('party', 'DEM'),
            ('year', '2012,2014'),
            ('candidate_id', 'H0VA08040,P80003338'),
        )

        for field, example in filter_fields:
            page = "/candidates?%s=%s" % (field, example)
            print page
            # returns at least one result
            results = self._results(page)
            self.assertGreater(len(results), 0)
            # doesn't return all results
            response = self._response(page)
            self.assertGreater(original_count, response['pagination']['count'])


    def test_name_endpoint_returns_unique_candidates_and_committees(self):
        results = self._results('/names?q=obama')
        cand_ids = [r['candidate_id'] for r in results if r['candidate_id']]
        self.assertEqual(len(cand_ids), len(set(cand_ids)))
        cmte_ids = [r['committee_id'] for r in results if r['committee_id']]
        self.assertEqual(len(cmte_ids), len(set(cmte_ids)))



    ## Committee ##
    def test_committee_list_fields(self):
        # example with committee
        response = self._response('/committees?committee_id=C00048587')
        result = response['results'][0]
        # main fields
        # original registration date doesn't make sense in this example, need to look into this more
        self.assertEqual(result['original_registration_date'], '1982-12-31 00:00:00')
        self.assertEqual(result['committee_type'], 'P')
        self.assertEqual(result['treasurer_name'], 'ROBERT J. LIPSHUTZ')
        self.assertEqual(result['party'], 'DEM')
        self.assertEqual(result['committee_type_full'], 'Presidential')
        self.assertEqual(result['name'], '1976 DEMOCRATIC PRESIDENTIAL CAMPAIGN COMMITTEE, INC. (PCC-1976 GENERAL ELECTION)')
        self.assertEqual(result['committee_id'], 'C00048587')
        self.assertEqual(result['designation_full'], 'Principal campaign committee')
        self.assertEqual(result['state'], 'GA')
        self.assertEqual(result['party_full'], 'Democratic Party')
        self.assertEqual(result['designation'], 'P')
        # no expired committees in test data to test just checking it exists
        self.assertEqual(result['expire_date'], None)
        # candidate fields
        candidate_result = response['results'][0]['candidates'][0]
        self.assertEqual(candidate_result['candidate_id'], 'P60000247')
        self.assertEqual(candidate_result['candidate_name'], 'CARTER, JIMMY')
        self.assertEqual(candidate_result['active_through'], 1980)
        self.assertEqual(candidate_result['link_date'], '2007-10-12 13:38:33')
        # Example with org type
        response = self._response('/committees?organization_type=C')
        results = response['results'][0]
        self.assertEqual(results['organization_type_full'], 'Corporation')
        self.assertEqual(results['organization_type'], 'C')

    def test_committee_detail_fields(self):
        response = self._response('/committee/C00048587')
        result = response['results'][0]
        # main fields
        self.assertEqual(result['original_registration_date'], '1982-12-31 00:00:00')
        self.assertEqual(result['committee_type'], 'P')
        self.assertEqual(result['treasurer_name'], 'ROBERT J. LIPSHUTZ')
        self.assertEqual(result['party'], 'DEM')
        self.assertEqual(result['committee_type_full'], 'Presidential')
        self.assertEqual(result['name'], '1976 DEMOCRATIC PRESIDENTIAL CAMPAIGN COMMITTEE, INC. (PCC-1976 GENERAL ELECTION)')
        self.assertEqual(result['committee_id'], 'C00048587')
        self.assertEqual(result['designation_full'], 'Principal campaign committee')
        self.assertEqual(result['state'], 'GA')
        self.assertEqual(result['party_full'], 'Democratic Party')
        self.assertEqual(result['designation'], 'P')
        # no expired committees in test data to test just checking it exists
        self.assertEqual(result['expire_date'], None)
        # candidate fields
        candidate_result = response['results'][0]['candidates'][0]
        self.assertEqual(candidate_result['candidate_id'], 'P60000247')
        self.assertEqual(candidate_result['candidate_name'], 'CARTER, JIMMY')
        self.assertEqual(candidate_result['active_through'], 1980)
        self.assertEqual(candidate_result['link_date'], '2007-10-12 13:38:33')
        # Things on the detailed view
        self.assertEqual(result['filing_frequency'], 'T')
        self.assertEqual(result['form_type'], 'F1Z')
        self.assertEqual(result['load_date'], '1982-12-31 00:00:00')
        self.assertEqual(result['street_1'], '1795 PEACHTREE ROAD , NE')
        self.assertEqual(result['zip'], '30309')
        # Example with org type
        response = self._response('/committees?organization_type=C')
        results = response['results'][0]
        self.assertEqual(results['organization_type_full'], 'Corporation')
        self.assertEqual(results['organization_type'], 'C')


    def test_committee_search_double_committee_id(self):
        response = self._response('/committees?committee_id=C00048587,C00116574&year=*')
        results = response['results']
        self.assertEqual(len(results), 2)

    def test_committee_search_filters(self):
        original_response = self._response('/committees')
        original_count = original_response['pagination']['count']

        party_response = self._response('/committees?party=REP')
        party_count = party_response['pagination']['count']
        self.assertEquals((original_count > party_count), True)

        committee_type_response = self._response('/committees?committee_type=P')
        committee_type_count = committee_type_response['pagination']['count']
        self.assertEquals((original_count > committee_type_count), True)

        name_response = self._response('/committees?name=Obama')
        name_count = name_response['pagination']['count']
        self.assertEquals((original_count > name_count), True)

        committee_id_response = self._response('/committees?committee_id=C00116574')
        committee_id_count = committee_id_response['pagination']['count']
        self.assertEquals((original_count > committee_id_count), True)

        designation_response = self._response('/committees?designation=P')
        designation_count = designation_response['pagination']['count']
        self.assertEquals((original_count > designation_count), True)

        state_response = self._response('/committees?state=CA')
        state_count = state_response['pagination']['count']
        self.assertEquals((original_count > state_count), True)


    def test2committees(self):
        response = self._results('/committee/C00484188?year=2012')
        self.assertEquals(len(response[0]['candidates']), 2)

    # /committees?
    def test_err_on_unsupported_arg(self):
        response = self.app.get('/committees?bogusArg=1')
        self.assertEquals(response.status_code, 400)

    def test_committee_party(self):
        response = self._results('/committees?party=REP')
        self.assertEquals(response[0]['party'], 'REP')
        self.assertEquals(response[0]['party_full'], 'Republican Party')

    def test_committee_filters(self):
        org_response = self._response('/committees')
        original_count = org_response['pagination']['count']

        # checking one example from each field
        filter_fields = (
            ('committee_id', 'C00484188,C00000422'),
            ('state', 'CA,DC'),
            ('name', 'Obama'),
            ('committee_type', 'S'),
            ('designation', 'P'),
            ('party', 'REP,DEM'),
            ('organization_type','C'),
        )

        for field, example in filter_fields:
            page = "/committees?%s=%s" % (field, example)
            print page
            # returns at least one result
            results = self._results(page)
            self.assertGreater(len(results), 0)
            # doesn't return all results
            response = self._response(page)
            self.assertGreater(original_count, response['pagination']['count'])

    def test_committees_by_cand_id(self):
        results =  self._results('/candidate/P60000247/committees')

        ids = [x['committee_id'] for x in results]

        self.assertIn('C00048587', ids)
        self.assertIn('C00111245', ids)
        self.assertIn('C00108407', ids)

    def test_committee_by_cand_filter(self):
        results =  self._results('/candidate/P60000247/committees?designation=P')
        self.assertEquals(1, len(results))

    def test_committee_by_candidate(self):
        results =  self._results('http://localhost:5000/candidate/P60000247/committees?year=*')
        self.assertEquals(3, len(results))

    def test_candidates_by_committee(self):
        results =  self._results('/committee/C00111245/candidates?year=*')
        self.assertEquals(1, len(results))

    @unittest.skip('This is not a great view anymore')
    def test_multiple_cmtes_in_detail(self):
        response = self._results('http://localhost:5000/candidate/P80003338/committees')
        self.assertEquals(len(response[0]), 11)
        self.assertEquals(response['pagination']['count'], 11)

# Totals
    @unittest.skip("not implemented yet")
    def test_reports_house_senate(self):
        results = self._results('/committee/C00002600/reports')

        fields = ('beginning_image_number', 'end_image_number', 'expire_date', 'load_date','report_type', 'report_type_full','report_year', 'type', 'cash_on_hand_beginning_period', 'cash_on_hand_end_period', 'debts_owed_by_committee', 'debts_owed_to_committee', 'operating_expenditures_period', 'other_political_committee_contributions_period', 'refunds_other_political_committee_contributions_period', 'total_disbursements_period', 'total_individual_contributions_period', 'total_receipts_period',)

        for field in fields:
            print field
            self.assertEquals(results[0]['reports'][0].has_key(field), True)

    @unittest.skip("not implemented yet")
    def test_reports_pac_party(self):
        results = self._results('/committee/C00000422/reports')

        fields = ('beginning_image_number', 'end_image_number', 'expire_date', 'load_date', 'report_type', 'report_type_full', 'report_year', 'total_disbursements_period', 'total_disbursements_summary_page_period', 'total_receipts_period', 'total_receipts_summary_page_period', 'type')

        for field in fields:
            print field
            self.assertEquals(results[0]['reports'][0].has_key(field), True)

    @unittest.skip("not implemented yet")
    def test_reports_presidental(self):
        results = self._results('/committee/C00347583/reports')

        fields = ('refunds_political_party_committee_contributions_period', 'other_receipts_period', 'total_disbursements_period', 'net_contributions_year', 'beginning_image_number', 'total_receipts_year', 'total_receipts', 'refunds_political_party_committee_contributions_year', 'total_loans_period', 'other_political_committee_contributions_year', 'loan_repayments_other_loans_period', 'net_contributions_period', 'refunds_other_political_committee_contributions_period', 'all_other_loans_year', 'net_operating_expenditures_period', 'loan_repayments_other_loans_year', 'total_individual_itemized_contributions_year', 'subtotal_period', 'other_receipts_year', 'total_contribution_refunds_col_total_period', 'debts_owed_by_committee', 'total_contribution_refunds_year', 'offsets_to_operating_expenditures_period', 'cash_on_hand_beginning_period', 'individual_itemized_contributions_period', 'refunds_individual_contributions_year', 'total_contributions_year', 'operating_expenditures_period', 'political_party_committee_contributions_year', 'total_individual_contributions_year', 'total_individual_unitemized_contributions_year', 'net_operating_expenditures_year', 'expire_date', 'individual_unitemized_contributions_period', 'transfers_to_other_authorized_committee_year', 'report_type', 'total_disbursements_year', 'type', 'operating_expenditures_year', 'transfers_from_other_authorized_committee_period', 'total_offsets_to_operating_expenditures_year', 'total_loan_repayments_year', 'candidate_contribution_year', 'refunds_other_political_committee_contributions_year', 'debts_owed_to_committee', 'other_disbursements_year', 'total_loan_repayments_period', 'candidate_contribution_period', 'transfers_to_other_authorized_committee_period', 'refunds_total_contributions_col_total_year', 'total_contributions_column_total_period', 'political_party_committee_contributions_period', 'cash_on_hand_end_period', 'all_other_loans_period', 'loans_made_by_candidate_year', 'total_individual_contributions_period', 'loans_made_by_candidate_period', 'total_offsets_to_operating_expenditures_period', 'offsets_to_operating_expenditures_year', 'total_contribution_refunds_period', 'report_year', 'total_loans_year', 'transfers_from_other_authorized_committee_year', 'load_date', 'other_disbursements_period', 'loan_repayments_candidate_loans_period', 'other_political_committee_contributions_period', 'total_receipts_period', 'total_contributions_period', 'end_image_number', 'refunds_individual_contributions_period', 'loan_repayments_candidate_loans_year', 'total_operating_expenditures_year', 'total_operating_expenditures_period', 'report_type_full', 'election_cycle',
            )

        for field in fields:
            print field
            self.assertEquals(results[0]['reports'][0].has_key(field), True)

    @unittest.skip("Not implementing for now.")
    def test_total_field_filter(self):
        results_disbursements = self._results('/committee/C00347583/totals?fields=disbursements')
        results_recipts = self._results('/committee/C00347583/totals?fields=total_receipts_period')

        self.assertIn('disbursements', results_disbursements[0]['totals'][0])
        self.assertIn('total_receipts_period',results_recipts[0]['reports'][0])
        self.assertNotIn('reports', results_disbursements[0])
        self.assertNotIn('totals', results_recipts[0])

    @unittest.skip("Not implementing for now.")
    def test_total_cycle(self):
        results1 = self._results('/committee/C00000422/totals?year=2004')
        total_receipts1 = results1[0]['receipts']

        results2 = self._results('/committee/C00000422/totals?year=2006')
        total_receipts2 = results2[0]['receipts']

        self.assertGreater(total_receipts2, total_receipts1)

    @unittest.skip("Not implementing for now.")
    def test_multiple_committee(self):
        results = self._results('/total?committee_id=C00002600,C00000422&fields=committtee_id')
        print len(results)
        self.assertEquals(len(results), 2)


    # Typeahead name search
    def test_typeahead_name_search(self):
        results = self._results('/names?q=oba')
        self.assertGreaterEqual(len(results), 10)
        for r in results:
            self.assertIn('OBA', r['name'])


