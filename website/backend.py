from flask import Flask, render_template, request
import json

app = Flask(__name__)


class InvestmentAllocation:
    def __init__(self, allocation_amount, investor_amounts):
        self.allocation_amount = allocation_amount
        self.investor_amounts = investor_amounts

    def __str__(self):
        return json.dumps({
            'allocation_amount': self.allocation_amount,
            'investor_amounts': self.investor_amounts
        })

    @staticmethod
    def proration_helper(allocation_amount, investor_amounts, historical_sum,
                         remaining_investors, existing_investor_allocations=None):
        calculated_allocations = existing_investor_allocations or {}
        remaining_investment_room = 0

        for investor_amount in investor_amounts:
            # if we have already got the maximum amount for an investor, skip
            investor_existing_allocation = calculated_allocations.get(investor_amount['name'], 0)
            if investor_existing_allocation == investor_amount['requested_amount']:
                continue

            prorated_investment = investor_existing_allocation

            if investor_amount['average_amount'] > 0:
                # add proration
                prorated_investment += allocation_amount * (investor_amount['average_amount'] / historical_sum)
            elif historical_sum == 0:
                # All remaining investors are new. Split investment equally
                prorated_investment += allocation_amount / remaining_investors
            # else, investor is the newest investor in the group, skip for now

            if prorated_investment > investor_amount['requested_amount']:
                remaining_investment_room += prorated_investment - investor_amount['requested_amount']
                prorated_investment = investor_amount['requested_amount']
            calculated_allocations[investor_amount['name']] = prorated_investment

        return calculated_allocations, remaining_investment_room

    def produce_allocations(self):
        """
        Produce allocations for investors.
        Will never allocate more than an investor's requested amount.
        """

        remaining_investment_room = self.allocation_amount

        calculated_investments = {}
        while remaining_investment_room > 0:
            # only examine investors that have not hit their limit
            historical_sum = 0
            remaining_investors = 0
            for investor_amount in self.investor_amounts:
                if calculated_investments.get(investor_amount['name'], 0) < investor_amount['requested_amount']:
                    historical_sum += investor_amount['average_amount']
                    remaining_investors += 1

            calculated_investments, remaining_investment_room = self.proration_helper(
                remaining_investment_room, self.investor_amounts, historical_sum,
                remaining_investors, calculated_investments)

        return calculated_investments


def run_tests():
    test_cases = ['complex_1', 'complex_2', 'simple_1', 'simple_2', 'raja_1', 'raja_2', 'raja_3', 'raja_4', 'raja_5',
                  'raja_6']
    for test_case in test_cases:
        input_file = open('./data/' + test_case + '_input.json')
        output_file = open('./data/' + test_case + '_output.json')
        input_data = json.load(input_file)
        output_data = json.load(output_file)

        inputInvestmentAllocation = InvestmentAllocation(input_data['allocation_amount'],
                                                         input_data['investor_amounts'])
        calculatedInvestmentAllocation = inputInvestmentAllocation.produce_allocations()

        if calculatedInvestmentAllocation != output_data:
            print("Test case " + test_case + " failed")
            print("Expected output: " + str(output_data))
            print("Actual output: " + str(calculatedInvestmentAllocation))
        else:
            print("Test case " + test_case + " passed")


def handle_investor_form_submission(investment_form_data):
    allocation_amount = int(investment_form_data.get('allocation_amount') or 0)
    if not allocation_amount:
        return None
    investor_amounts = []

    for investor_id in range(10):
        investor_name = investment_form_data.get('investor_name_' + str(investor_id))
        if not investor_name:
            break

        requested_amount = int(investment_form_data.get('requested_amount_' + str(investor_id)) or 0)
        average_amount = int(investment_form_data.get('average_amount_' + str(investor_id)) or 0)

        investor = {
            'name': investor_name,
            'requested_amount': requested_amount,
            'average_amount': average_amount,
        }

        investor_amounts.append(investor)

    investment_allocation = InvestmentAllocation(allocation_amount, investor_amounts)
    return investment_allocation.produce_allocations()


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        calculated_allocations = handle_investor_form_submission(request.form)
        return render_template('calculator.html', calculated_allocations=calculated_allocations)

    return render_template('calculator.html')
