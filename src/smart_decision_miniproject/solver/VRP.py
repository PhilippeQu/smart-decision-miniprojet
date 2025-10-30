import random
import math
import time
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class Customer:
    """客户点信息"""
    id: int
    x: float
    y: float
    demand: int
    ready_time: int
    due_time: int
    service_time: int


class SolomonDataParser:
    """Solomon数据格式解析器"""
    
    @staticmethod
    def parse_solomon_file(file_content: str) -> Tuple[List[Customer], Dict[str, int]]:
        """解析Solomon格式的VRP数据文件
        
        Args:
            file_content: 文件内容字符串
            
        Returns:
            Tuple[List[Customer], Dict[str, int]]: 客户列表和参数字典
        """
        lines = file_content.strip().split('\n')
        customers = []
        params = {}
        
        # 解析文件头信息
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # 查找车辆数量和容量信息
            if 'NUMBER' in line.upper() and 'CAPACITY' in line.upper():
                parts = line.split()
                if len(parts) >= 4:
                    params['num_vehicles'] = int(parts[1])
                    params['vehicle_capacity'] = int(parts[3])
            
            # 查找客户数据开始位置 - 更灵活的匹配
            if ('CUST NO.' in line.upper() or 'XCOORD' in line.upper() or 
                'CUSTOMER' in line.upper() or line.upper().startswith('CUST')):
                # 从下一行开始解析客户数据
                for j in range(i + 1, len(lines)):
                    customer_line = lines[j].strip()
                    if not customer_line:
                        continue
                    
                    # 跳过空行和非数字开头的行
                    if not customer_line[0].isdigit():
                        continue
                    
                    # 解析客户数据，去除多余空格
                    parts = customer_line.split()
                    if len(parts) >= 7:
                        try:
                            customer = Customer(
                                id=int(parts[0]),
                                x=float(parts[1]),
                                y=float(parts[2]),
                                demand=int(parts[3]),
                                ready_time=int(parts[4]),
                                due_time=int(parts[5]),
                                service_time=int(parts[6])
                            )
                            customers.append(customer)
                        except (ValueError, IndexError) as e:
                            print(f"警告: 跳过无效的客户数据行: {customer_line} - {e}")
                            continue
                break
        
        # 设置默认参数
        if 'num_vehicles' not in params:
            params['num_vehicles'] = max(1, len(customers) // 10)  # 默认车辆数
        if 'vehicle_capacity' not in params:
            params['vehicle_capacity'] = 200  # 默认容量
            
        return customers, params


class VRPResult:
    """VRP求解结果"""
    
    def __init__(self, routes: List[List[int]], total_distance: float, 
                 customers: List[Customer], solve_time: float = 0.0):
        self.routes = routes
        self.total_distance = total_distance
        self.customers = customers
        self.solve_time = solve_time
        self.num_vehicles_used = len([r for r in routes if r])
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取求解统计信息"""
        if not self.routes:
            return {
                'num_vehicles_used': 0,
                'total_distance': 0.0,
                'total_customers': 0,
                'average_route_length': 0.0,
                'solve_time': self.solve_time
            }
        
        active_routes = [r for r in self.routes if r]
        route_lengths = [len(route) for route in active_routes]
        total_customers = sum(route_lengths)
        
        return {
            'num_vehicles_used': self.num_vehicles_used,
            'total_distance': round(self.total_distance, 2),
            'total_customers': total_customers,
            'average_route_length': round(total_customers / self.num_vehicles_used, 2) if self.num_vehicles_used > 0 else 0,
            'solve_time': round(self.solve_time, 3),
            'routes_details': [
                {
                    'route_id': i + 1,
                    'customers': route,
                    'num_customers': len(route),
                    'route_distance': round(self._calculate_route_distance(route), 2),
                    'total_demand': sum(self.customers[j].demand for j in route) if route else 0
                }
                for i, route in enumerate(active_routes)
            ]
        }
    
    def _calculate_route_distance(self, route: List[int]) -> float:
        """计算单条路径的距离"""
        if not route:
            return 0.0
            
        total_distance = 0.0
        # 从仓库到第一个客户
        if route:
            depot = self.customers[0]
            first_customer = self.customers[route[0]]
            dx = depot.x - first_customer.x
            dy = depot.y - first_customer.y
            total_distance += math.sqrt(dx * dx + dy * dy)
        
        # 客户之间的距离
        for i in range(len(route) - 1):
            customer_i = self.customers[route[i]]
            customer_j = self.customers[route[i + 1]]
            dx = customer_i.x - customer_j.x
            dy = customer_i.y - customer_j.y
            total_distance += math.sqrt(dx * dx + dy * dy)
        
        # 从最后一个客户回到仓库
        if route:
            last_customer = self.customers[route[-1]]
            depot = self.customers[0]
            dx = last_customer.x - depot.x
            dy = last_customer.y - depot.y
            total_distance += math.sqrt(dx * dx + dy * dy)
            
        return total_distance
    
    def to_dict(self) -> Dict[str, Any]:
        """将结果转换为字典格式"""
        return {
            'routes': self.routes,
            'total_distance': self.total_distance,
            'num_vehicles_used': self.num_vehicles_used,
            'solve_time': self.solve_time,
            'statistics': self.get_statistics()
        }


class BaseVRPSolver:
    """Base class for VRP solvers."""

    def __init__(
        self,
        distance_matrix: List[List[float]],
        demands: List[float],
        vehicle_capacity: float,
        num_vehicles: int,
        depot_index: int = 0
    ):
        """Initialize the VRP solver.
        
        Args:
            distance_matrix: Square matrix of distances between locations
            demands: Demand for each customer (depot demand should be 0)
            vehicle_capacity: Maximum capacity for each vehicle
            num_vehicles: Number of available vehicles
            depot_index: Index of the depot (default: 0)
        """
        self.distance_matrix = distance_matrix
        self.demands = demands
        self.vehicle_capacity = vehicle_capacity
        self.num_vehicles = num_vehicles
        self.depot_index = depot_index
        self.num_customers = len(distance_matrix) - 1  # Excluding depot
        self.num_locations = len(distance_matrix)

    def solve_vrp(self) -> List[List[int]]:
        """Solve the Vehicle Routing Problem.
        
        Returns:
            List of routes, where each route is a list of customer indices
        """
        return []  # Default implementation returns empty routes


class GeneticAlgorithmVRPSolver(BaseVRPSolver):
    """VRP solver using Genetic Algorithm."""

    def __init__(
        self,
        distance_matrix: List[List[float]],
        demands: List[float],
        vehicle_capacity: float,
        num_vehicles: int,
        depot_index: int = 0,
        population_size: int = 100,
        num_generations: int = 500,
        mutation_rate: float = 0.02,
        crossover_rate: float = 0.8,
        elite_ratio: float = 0.1
    ):
        """Initialize the Genetic Algorithm VRP solver.
        
        Args:
            distance_matrix: Square matrix of distances between locations
            demands: Demand for each customer
            vehicle_capacity: Maximum capacity for each vehicle
            num_vehicles: Number of available vehicles
            depot_index: Index of the depot
            population_size: Size of the population
            num_generations: Number of generations to evolve
            mutation_rate: Probability of mutation
            crossover_rate: Probability of crossover
            elite_ratio: Ratio of elite individuals to preserve
        """
        super().__init__(distance_matrix, demands, vehicle_capacity, num_vehicles, depot_index)
        self.population_size = population_size
        self.num_generations = num_generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_ratio = elite_ratio
        self.elite_size = int(population_size * elite_ratio)

    def calculate_route_distance(self, route: List[int]) -> float:
        """Calculate the total distance of a route including depot visits.
        
        Args:
            route: List of customer indices in the route
            
        Returns:
            Total distance of the route
        """
        if not route:
            return 0.0
            
        total_distance = 0.0
        # Distance from depot to first customer
        total_distance += self.distance_matrix[self.depot_index][route[0]]
        
        # Distance between consecutive customers
        for i in range(len(route) - 1):
            total_distance += self.distance_matrix[route[i]][route[i + 1]]
        
        # Distance from last customer back to depot
        total_distance += self.distance_matrix[route[-1]][self.depot_index]
        
        return total_distance

    def calculate_solution_fitness(self, solution: List[List[int]]) -> float:
        """Calculate the fitness of a solution (lower is better).
        
        Args:
            solution: List of routes
            
        Returns:
            Total distance of all routes
        """
        total_distance = 0.0
        for route in solution:
            total_distance += self.calculate_route_distance(route)
        return total_distance

    def is_solution_feasible(self, solution: List[List[int]]) -> bool:
        """Check if a solution is feasible (capacity constraints).
        
        Args:
            solution: List of routes
            
        Returns:
            True if solution is feasible, False otherwise
        """
        # Check if all customers are visited exactly once
        visited_customers = set()
        for route in solution:
            for customer in route:
                if customer in visited_customers:
                    return False  # Customer visited more than once
                visited_customers.add(customer)
        
        # Check if all customers (except depot) are visited
        expected_customers = set(range(self.num_locations))
        expected_customers.remove(self.depot_index)
        if visited_customers != expected_customers:
            return False
        
        # Check capacity constraints
        for route in solution:
            route_demand = sum(self.demands[customer] for customer in route)
            if route_demand > self.vehicle_capacity:
                return False
                
        return True

    def generate_random_solution(self) -> List[List[int]]:
        """Generate a random feasible solution.
        
        Returns:
            Random solution as list of routes
        """
        # Get all customers (excluding depot)
        customers = [i for i in range(self.num_locations) if i != self.depot_index]
        random.shuffle(customers)
        
        routes = []
        current_route = []
        current_demand = 0.0
        
        for customer in customers:
            customer_demand = self.demands[customer]
            
            # If adding this customer exceeds capacity, start a new route
            if current_demand + customer_demand > self.vehicle_capacity:
                if current_route:  # Only add non-empty routes
                    routes.append(current_route)
                current_route = [customer]
                current_demand = customer_demand
            else:
                current_route.append(customer)
                current_demand += customer_demand
        
        # Add the last route if not empty
        if current_route:
            routes.append(current_route)
        
        # If we have more routes than vehicles, merge some routes
        while len(routes) > self.num_vehicles and len(routes) > 1:
            # Find two routes that can be merged
            merged = False
            for i in range(len(routes)):
                for j in range(i + 1, len(routes)):
                    total_demand = (sum(self.demands[c] for c in routes[i]) + 
                                  sum(self.demands[c] for c in routes[j]))
                    if total_demand <= self.vehicle_capacity:
                        # Merge routes j into i
                        routes[i].extend(routes[j])
                        routes.pop(j)
                        merged = True
                        break
                if merged:
                    break
            
            if not merged:
                break  # Cannot merge any more routes
        
        return routes

    def generate_initial_population(self) -> List[List[List[int]]]:
        """Generate initial population.
        
        Returns:
            List of solutions (population)
        """
        population = []
        for _ in range(self.population_size):
            solution = self.generate_random_solution()
            population.append(solution)
        return population

    def tournament_selection(self, population: List[List[List[int]]], tournament_size: int = 3) -> List[List[int]]:
        """Select a parent using tournament selection.
        
        Args:
            population: Current population
            tournament_size: Number of individuals in tournament
            
        Returns:
            Selected parent solution
        """
        tournament = random.sample(population, min(tournament_size, len(population)))
        best_solution = min(tournament, key=self.calculate_solution_fitness)
        return best_solution

    def order_crossover(self, parent1: List[List[int]], parent2: List[List[int]]) -> Tuple[List[List[int]], List[List[int]]]:
        """Perform Order Crossover (OX) adapted for VRP.
        
        Args:
            parent1: First parent solution
            parent2: Second parent solution
            
        Returns:
            Two offspring solutions
        """
        # Flatten parents to get customer sequences
        customers1 = []
        customers2 = []
        for route in parent1:
            customers1.extend(route)
        for route in parent2:
            customers2.extend(route)
        
        if len(customers1) != len(customers2):
            # If parents have different structures, return copies
            return [route[:] for route in parent1], [route[:] for route in parent2]
        
        n = len(customers1)
        if n <= 2:
            return [route[:] for route in parent1], [route[:] for route in parent2]
        
        # Perform order crossover on flattened sequences
        point1 = random.randint(0, n // 2)
        point2 = random.randint(point1 + 1, n)
        
        offspring1 = [-1] * n
        offspring2 = [-1] * n
        
        # Copy segments
        offspring1[point1:point2] = customers1[point1:point2]
        offspring2[point1:point2] = customers2[point1:point2]
        
        # Fill remaining positions
        def fill_offspring(offspring, other_parent):
            remaining = [c for c in other_parent if c not in offspring]
            pos = 0
            for i in range(n):
                if offspring[i] == -1:
                    offspring[i] = remaining[pos]
                    pos += 1
        
        fill_offspring(offspring1, customers2)
        fill_offspring(offspring2, customers1)
        
        # Convert back to route format
        def customers_to_routes(customers):
            routes = []
            current_route = []
            current_demand = 0.0
            
            for customer in customers:
                customer_demand = self.demands[customer]
                if current_demand + customer_demand > self.vehicle_capacity:
                    if current_route:
                        routes.append(current_route)
                    current_route = [customer]
                    current_demand = customer_demand
                else:
                    current_route.append(customer)
                    current_demand += customer_demand
            
            if current_route:
                routes.append(current_route)
            return routes
        
        return customers_to_routes(offspring1), customers_to_routes(offspring2)

    def mutate_solution(self, solution: List[List[int]]) -> List[List[int]]:
        """Mutate a solution using various mutation operators.
        
        Args:
            solution: Solution to mutate
            
        Returns:
            Mutated solution
        """
        if random.random() > self.mutation_rate:
            return [route[:] for route in solution]  # No mutation
        
        mutated = [route[:] for route in solution]
        
        # Choose mutation type randomly
        mutation_type = random.choice(['swap', 'insert', 'invert'])
        
        if mutation_type == 'swap':
            # Swap two customers (possibly between different routes)
            all_customers = []
            route_indices = []
            for i, route in enumerate(mutated):
                for j, customer in enumerate(route):
                    all_customers.append((i, j, customer))
                    route_indices.append(i)
            
            if len(all_customers) >= 2:
                idx1, idx2 = random.sample(range(len(all_customers)), 2)
                route1, pos1, customer1 = all_customers[idx1]
                route2, pos2, customer2 = all_customers[idx2]
                
                # Swap customers
                mutated[route1][pos1] = customer2
                mutated[route2][pos2] = customer1
        
        elif mutation_type == 'insert':
            # Move a customer to a different position
            non_empty_routes = [i for i, route in enumerate(mutated) if route]
            if non_empty_routes:
                route_idx = random.choice(non_empty_routes)
                route = mutated[route_idx]
                if len(route) > 1:
                    pos1 = random.randint(0, len(route) - 1)
                    customer = route.pop(pos1)
                    pos2 = random.randint(0, len(route))
                    route.insert(pos2, customer)
        
        elif mutation_type == 'invert':
            # Invert a segment within a route
            non_empty_routes = [i for i, route in enumerate(mutated) if len(route) >= 2]
            if non_empty_routes:
                route_idx = random.choice(non_empty_routes)
                route = mutated[route_idx]
                if len(route) >= 2:
                    pos1 = random.randint(0, len(route) - 2)
                    pos2 = random.randint(pos1 + 1, len(route) - 1)
                    route[pos1:pos2+1] = reversed(route[pos1:pos2+1])
        
        # Ensure the mutated solution is still feasible
        if not self.is_solution_feasible(mutated):
            return [route[:] for route in solution]  # Return original if infeasible
        
        return mutated

    def solve_vrp(self) -> List[List[int]]:
        """Solve VRP using Genetic Algorithm.
        
        Returns:
            Best solution found as list of routes
        """
        print("Starting Genetic Algorithm for VRP...")
        
        # Generate initial population
        population = self.generate_initial_population()
        
        # Track best solution
        best_solution = None
        best_fitness = float('inf')
        
        for generation in range(self.num_generations):
            # Calculate fitness for all individuals
            fitness_scores = []
            for solution in population:
                fitness = self.calculate_solution_fitness(solution)
                fitness_scores.append(fitness)
                
                if fitness < best_fitness:
                    best_fitness = fitness
                    best_solution = [route[:] for route in solution]
            
            # Create new population
            new_population = []
            
            # Elitism: keep best individuals
            elite_indices = sorted(range(len(fitness_scores)), key=lambda i: fitness_scores[i])[:self.elite_size]
            for idx in elite_indices:
                new_population.append([route[:] for route in population[idx]])
            
            # Generate offspring
            while len(new_population) < self.population_size:
                parent1 = self.tournament_selection(population)
                parent2 = self.tournament_selection(population)
                
                if random.random() < self.crossover_rate:
                    offspring1, offspring2 = self.order_crossover(parent1, parent2)
                else:
                    offspring1 = [route[:] for route in parent1]
                    offspring2 = [route[:] for route in parent2]
                
                # Mutate offspring
                offspring1 = self.mutate_solution(offspring1)
                offspring2 = self.mutate_solution(offspring2)
                
                new_population.extend([offspring1, offspring2])
            
            # Trim population to exact size
            population = new_population[:self.population_size]
            
            # Print progress
            if generation % 50 == 0:
                print(f"Generation {generation}: Best fitness = {best_fitness:.2f}")
        
        print(f"Final best fitness: {best_fitness:.2f}")
        return best_solution if best_solution is not None else []


def solve_solomon_vrp(file_content: str) -> VRPResult:
    """求解Solomon VRP实例的主函数
    
    Args:
        file_content: Solomon格式的文件内容
        
    Returns:
        VRPResult: 求解结果
    """
    start_time = time.time()
    
    # 解析数据
    customers, params = SolomonDataParser.parse_solomon_file(file_content)
    
    if not customers:
        return VRPResult([], 0.0, [], 0.0)
    
    # 构建距离矩阵
    n = len(customers)
    distance_matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    demands = []
    
    for i in range(n):
        demands.append(float(customers[i].demand))
        for j in range(n):
            if i != j:
                dx = customers[i].x - customers[j].x
                dy = customers[i].y - customers[j].y
                distance_matrix[i][j] = math.sqrt(dx * dx + dy * dy)
    
    # 创建求解器
    solver = GeneticAlgorithmVRPSolver(
        distance_matrix=distance_matrix,
        demands=demands,
        vehicle_capacity=float(params['vehicle_capacity']),
        num_vehicles=params['num_vehicles'],
        depot_index=0,
        population_size=50,
        num_generations=100,
        mutation_rate=0.02,
        crossover_rate=0.8,
        elite_ratio=0.1
    )
    
    # 求解
    routes = solver.solve_vrp()
    
    # 计算总距离
    total_distance = solver.calculate_solution_fitness(routes)
    
    solve_time = time.time() - start_time
    
    return VRPResult(routes, total_distance, customers, solve_time)


def main():
    """Example usage of the Genetic Algorithm VRP solver."""
    
    # Example problem: 5 customers + 1 depot
    # Locations: Depot(0), Customer1(1), Customer2(2), Customer3(3), Customer4(4), Customer5(5)
    distance_matrix = [
        [0.0, 10.0, 15.0, 20.0, 25.0, 30.0],  # From depot
        [10.0, 0.0, 8.0, 12.0, 18.0, 25.0],   # From customer 1
        [15.0, 8.0, 0.0, 10.0, 15.0, 20.0],   # From customer 2
        [20.0, 12.0, 10.0, 0.0, 8.0, 15.0],   # From customer 3
        [25.0, 18.0, 15.0, 8.0, 0.0, 10.0],   # From customer 4
        [30.0, 25.0, 20.0, 15.0, 10.0, 0.0],  # From customer 5
    ]
    
    # Customer demands (depot demand is 0)
    demands = [0.0, 10.0, 8.0, 12.0, 15.0, 9.0]
    
    # Vehicle parameters
    vehicle_capacity = 25.0  # Each vehicle can carry up to 25 units
    num_vehicles = 3
    
    print("=== Vehicle Routing Problem with Genetic Algorithm ===")
    print(f"Number of customers: {len(demands) - 1}")
    print(f"Vehicle capacity: {vehicle_capacity}")
    print(f"Number of vehicles: {num_vehicles}")
    print(f"Customer demands: {demands[1:]}")
    print("-" * 60)
    
    # Create and run solver
    solver = GeneticAlgorithmVRPSolver(
        distance_matrix=distance_matrix,
        demands=demands,
        vehicle_capacity=vehicle_capacity,
        num_vehicles=num_vehicles,
        depot_index=0,
        population_size=50,
        num_generations=200,
        mutation_rate=0.02,
        crossover_rate=0.8,
        elite_ratio=0.1
    )
    
    best_solution = solver.solve_vrp()
    
    print("\n=== Best Solution Found ===")
    total_distance = 0.0
    total_demand_served = 0.0
    
    for i, route in enumerate(best_solution):
        if route:  # Only show non-empty routes
            route_distance = solver.calculate_route_distance(route)
            route_demand = sum(demands[customer] for customer in route)
            total_distance += route_distance
            total_demand_served += route_demand
            
            route_str = f"Depot -> {' -> '.join(map(str, route))} -> Depot"
            print(f"Vehicle {i+1}: {route_str}")
            print(f"  Distance: {route_distance:.2f}")
            print(f"  Demand: {route_demand:.2f}/{vehicle_capacity}")
            print()
    
    print(f"Total distance: {total_distance:.2f}")
    print(f"Total demand served: {total_demand_served:.2f}")
    print(f"Number of vehicles used: {len([r for r in best_solution if r])}")
    
    # Verify solution feasibility
    if solver.is_solution_feasible(best_solution):
        print("✓ Solution is feasible!")
    else:
        print("✗ Solution is not feasible!")


if __name__ == "__main__":
    main()
