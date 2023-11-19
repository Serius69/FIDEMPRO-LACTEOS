import random
class MilkProduction:
    def __init__(self, production_capacity):
        self.production_capacity = production_capacity
        self.production_queue = 0

    def produce_milk(self, quantity):
        if quantity <= self.production_capacity:
            self.production_queue += quantity
            return True
        else:
            return False

    def process_production(self):
        # Simulate the production process
        if self.production_queue > 0:
            produced = random.randint(1, self.production_queue)
            self.production_queue -= produced
            return produced
        return 0

class MilkInventory:
    def __init__(self):
        self.inventory = 0

    def add_to_inventory(self, quantity):
        self.inventory += quantity

    def inspect_milk(self):
        # Simulate milk inspection, e.g., quality control
        good_quality = random.choice([True, False])
        if good_quality:
            return self.inventory
        else:
            self.inventory = 0
            return 0

class MilkDistribution:
    def __init__(self):
        self.distributed = 0

    def distribute_milk(self, quantity):
        # Simulate milk distribution to retailers
        self.distributed += quantity

class MilkMarketing:
    def create_marketing_campaign(self):
        # Simulate marketing efforts, e.g., advertising
        print("Marketing campaign created.")

class MilkSales:
    def __init__(self, price_per_unit):
        self.price_per_unit = price_per_unit

    def sell_milk(self, quantity):
        # Simulate milk sales
        revenue = quantity * self.price_per_unit
        return revenue

class MilkCompetence:
    def evaluate_competition(self):
        # Simulate competition analysis
        competitors = ["Competitor A", "Competitor B", "Competitor C"]
        return random.choice(competitors)
production_capacity = 100
price_per_unit = 2.5

production = MilkProduction(production_capacity)
inventory = MilkInventory()
distribution = MilkDistribution()
marketing = MilkMarketing()
sales = MilkSales(price_per_unit)
competence = MilkCompetence()

days = 7
for day in range(1, days + 1):
    print(f"Day {day}:")

    production.produce_milk(production_capacity)
    produced = production.process_production()
    inventory.add_to_inventory(produced)

    inspected = inventory.inspect_milk()
    print(f"Produced: {produced} units")
    print(f"Available in inventory: {inspected} units")

    distribution.distribute_milk(inspected)
    print(f"Distributed: {distribution.distributed} units")

    marketing.create_marketing_campaign()

    sold = random.randint(10, 50)
    revenue = sales.sell_milk(sold)
    print(f"Sold: {sold} units, Revenue: ${revenue:.2f}")

    competitor = competence.evaluate_competition()
    print(f"Competing with: {competitor}\n")

print("Simulation Complete")
