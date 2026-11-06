def calculate_slab_tax(income, slabs):

    if income < 0:
        raise ValueError("Income cannot be negative")

    total_tax = 0
    previous_limit = 0

    for upper_limit, tax_rate in slabs:

        taxable_amount = min(income, upper_limit) - previous_limit

        if taxable_amount <= 0:
            break

        total_tax += taxable_amount * tax_rate

        previous_limit = upper_limit

        if income <= upper_limit:
            break

    return total_tax