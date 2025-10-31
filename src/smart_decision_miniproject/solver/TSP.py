import random
import math

from smart_decision_miniproject.TSP_datamodel import DistanceMatrix
from smart_decision_miniproject.TSP_datamodel import (
    RandomDistanceMatrixFactory,
)
from smart_decision_miniproject.timer import Timer
from smart_decision_miniproject.timer.timer_manager import TimerManager

class BaseTSPSolver:
    """Base class for TSP solvers."""

    def __init__(self, distance_matrix: DistanceMatrix):
        self.distance_matrix = distance_matrix

    def solveTSP(self) -> list[int]:

        return []


class SimulatedAnnealingTSPSolver(BaseTSPSolver):
    """TSP solver using the simulated annealing algorithm."""

    def __init__(
        self,
        distance_matrix: DistanceMatrix = DistanceMatrix(0),
        initial_temperature: float = 1000.0,
        min_temperature: float = 0.01,
        cooling_rate: float = 0.995,
        max_iterations: int = 10000,
    ):
        """Initialize the simulated annealing TSP solver.

        Args:
            distance_matrix (list[list[float]]): A square matrix representing distances between cities.
            initial_temperature (float): Starting temperature for the annealing process.
            min_temperature (float): Minimum temperature to stop the algorithm.
            cooling_rate (float): Rate at which temperature decreases (0 < cooling_rate < 1).
            max_iterations (int): Maximum number of iterations to run.
        """
        super().__init__(distance_matrix)
        self.initial_temperature = initial_temperature
        self.min_temperature = min_temperature
        self.cooling_rate = cooling_rate
        self.max_iterations = max_iterations
        self.num_cities = len(distance_matrix)
    
    def update_distance_matrix(self, distance_matrix: DistanceMatrix):
        """Update the distance matrix and recalculate num_cities."""
        self.distance_matrix = distance_matrix
        self.num_cities = len(distance_matrix)

    def calculate_tour_distance(self, tour: list[int]) -> float:
        """Calculate the total distance of a tour.

        Args:
            tour (list[int]): A list of city indices representing a tour.

        Returns:
            float: Total distance of the tour.
        """
        total_distance = self.distance_matrix.cal_tour_distance(tour)
        return total_distance

    def generate_initial_solution(self) -> list[int]:
        """Generate an initial random solution starting from city 0 (A).

        Returns:
            list[int]: A random permutation of city indices starting with city 0.
        """
        # Start with city 0 (A), then shuffle the remaining cities
        remaining_cities = list(range(1, self.num_cities))
        random.shuffle(remaining_cities)
        return [0] + remaining_cities

    def get_neighbor(self, tour: list[int]) -> list[int]:
        """Generate a neighboring solution by swapping two random cities.
        Keep city 0 (A) fixed at the first position.

        Args:
            tour (list[int]): Current tour.

        Returns:
            list[int]: A neighboring tour with two cities swapped (excluding city 0).
        """
        new_tour = tour.copy()
        # Only swap cities from index 1 onwards (keep city 0 fixed)
        if len(tour) > 2:  # Need at least 3 cities to swap
            i, j = random.sample(range(1, len(tour)), 2)
            new_tour[i], new_tour[j] = new_tour[j], new_tour[i]
        return new_tour

    def accept_solution(
        self, current_distance: float, new_distance: float, temperature: float
    ) -> bool:
        """Determine whether to accept a new solution based on the acceptance probability.

        Args:
            current_distance (float): Distance of the current solution.
            new_distance (float): Distance of the new solution.
            temperature (float): Current temperature.

        Returns:
            bool: True if the new solution should be accepted, False otherwise.
        """
        if new_distance < current_distance:
            return True

        # Accept worse solutions with probability based on temperature
        delta = new_distance - current_distance
        probability = math.exp(-delta / temperature)
        return random.random() < probability

    def solveTSP(self) -> list[int]:
        """Solve the TSP using simulated annealing algorithm.

        Returns:
            list[int]: A list of city indices representing the best tour found.
        """
        # Initialize solution
        current_tour = self.generate_initial_solution()
        current_distance = self.calculate_tour_distance(current_tour)

        # Keep track of the best solution found
        best_tour = current_tour.copy()
        best_distance = current_distance

        # Initialize temperature
        temperature = self.initial_temperature

        iteration = 0
        while temperature > self.min_temperature and iteration < self.max_iterations:
            # Generate a neighboring solution
            new_tour = self.get_neighbor(current_tour)
            new_distance = self.calculate_tour_distance(new_tour)

            # Decide whether to accept the new solution
            if self.accept_solution(current_distance, new_distance, temperature):
                current_tour = new_tour
                current_distance = new_distance

                # Update best solution if necessary
                if current_distance < best_distance:
                    best_tour = current_tour.copy()
                    best_distance = current_distance

            # Cool down the temperature
            temperature *= self.cooling_rate
            iteration += 1

        return best_tour

class AntColonyOptimizationTSPSolver(BaseTSPSolver):
    """TSP solver using the Ant Colony Optimization algorithm."""

    def __init__(
        self,
        distance_matrix: DistanceMatrix = DistanceMatrix(0),
        num_ants: int = 10,
        alpha: float = 1.0,
        beta: float = 2.0,
        evaporation_rate: float = 0.5,
        Q: float = 100.0,
        num_iterations: int = 100,
        convergence_threshold: float = 1e-6,
        patience: int = 10,
    ):
        """Initialize the Ant Colony Optimization TSP solver.

        Args:
            distance_matrix (list[list[float]]): A square matrix representing distances between cities.
            num_ants (int): Number of ants in the colony.
            num_iterations (int): Maximum number of iterations to run the algorithm.
            alpha (float): Importance of pheromone trails (α).
            beta (float): Importance of heuristic information (β).
            evaporation_rate (float): Rate of pheromone evaporation (ρ).
            Q (float): Pheromone deposit factor.
            convergence_threshold (float): Minimum improvement threshold for convergence detection.
            patience (int): Number of iterations without improvement before stopping.
        """
        super().__init__(distance_matrix)
        self.num_ants = num_ants
        self.num_iterations = num_iterations
        self.alpha = alpha
        self.beta = beta
        self.evaporation_rate = evaporation_rate
        self.Q = Q
        self.convergence_threshold = convergence_threshold
        self.patience = patience
        self.num_cities = len(distance_matrix)
        
        # Initialize pheromone matrix
        self.pheromone = [[1.0 for _ in range(self.num_cities)] for _ in range(self.num_cities)]
        
        # Calculate heuristic information (visibility) matrix
        self.visibility = self._calculate_visibility_matrix()
    
    def update_distance_matrix(self, distance_matrix: DistanceMatrix):
        """Update the distance matrix and reinitialize all dependent structures."""
        self.distance_matrix = distance_matrix
        self.num_cities = len(distance_matrix)
        
        # Reinitialize pheromone matrix
        self.pheromone = [[1.0 for _ in range(self.num_cities)] for _ in range(self.num_cities)]
        
        # Recalculate visibility matrix
        self.visibility = self._calculate_visibility_matrix()

    def _calculate_visibility_matrix(self) -> list[list[float]]:
        """Calculate the visibility matrix (1/distance).
        
        Returns:
            list[list[float]]: Visibility matrix where visibility[i][j] = 1/distance[i][j].
        """
        visibility = [[0.0 for _ in range(self.num_cities)] for _ in range(self.num_cities)]
        for i in range(self.num_cities):
            for j in range(self.num_cities):
                if i != j and self.distance_matrix[i][j] > 0:
                    visibility[i][j] = 1.0 / self.distance_matrix[i][j]
        return visibility

    def calculate_tour_distance(self, tour: list[int]) -> float:
        """Calculate the total distance of a tour.

        Args:
            tour (list[int]): A list of city indices representing a tour.

        Returns:
            float: Total distance of the tour.
        """
        total_distance = 0.0
        for i in range(len(tour)):
            from_city = tour[i]
            to_city = tour[(i + 1) % len(tour)]
            total_distance += self.distance_matrix[from_city][to_city]
        return total_distance

    def _select_next_city(self, current_city: int, unvisited_cities: list[int]) -> int:
        """Select the next city for an ant to visit based on pheromone and heuristic information.

        Args:
            current_city (int): Current city index.
            unvisited_cities (list[int]): List of unvisited city indices.

        Returns:
            int: Index of the next city to visit.
        """
        if not unvisited_cities:
            return current_city

        # Calculate probabilities for each unvisited city
        probabilities = []
        total_probability = 0.0

        for city in unvisited_cities:
            pheromone_factor = self.pheromone[current_city][city] ** self.alpha
            visibility_factor = self.visibility[current_city][city] ** self.beta
            probability = pheromone_factor * visibility_factor
            probabilities.append(probability)
            total_probability += probability

        # Normalize probabilities
        if total_probability > 0:
            probabilities = [p / total_probability for p in probabilities]
        else:
            # If all probabilities are 0, choose randomly
            probabilities = [1.0 / len(unvisited_cities) for _ in unvisited_cities]

        # Select city based on probabilities (roulette wheel selection)
        rand = random.random()
        cumulative_probability = 0.0
        for i, probability in enumerate(probabilities):
            cumulative_probability += probability
            if rand <= cumulative_probability:
                return unvisited_cities[i]

        # Fallback: return the last city
        return unvisited_cities[-1]

    def _construct_ant_tour(self) -> list[int]:
        """Construct a tour for a single ant starting from city 0.

        Returns:
            list[int]: A tour constructed by the ant.
        """
        tour = [0]  # Start from city 0 (A)
        unvisited_cities = list(range(1, self.num_cities))

        while unvisited_cities:
            current_city = tour[-1]
            next_city = self._select_next_city(current_city, unvisited_cities)
            tour.append(next_city)
            unvisited_cities.remove(next_city)

        return tour

    def _update_pheromones(self, ant_tours: list[list[int]], ant_distances: list[float]):
        """Update pheromone levels based on ant tours.

        Args:
            ant_tours (list[list[int]]): List of tours constructed by ants.
            ant_distances (list[float]): List of distances for each ant tour.
        """
        # Evaporation
        for i in range(self.num_cities):
            for j in range(self.num_cities):
                self.pheromone[i][j] *= (1.0 - self.evaporation_rate)

        # Pheromone deposit
        for tour, distance in zip(ant_tours, ant_distances):
            if distance > 0:
                pheromone_deposit = self.Q / distance
                for i in range(len(tour)):
                    from_city = tour[i]
                    to_city = tour[(i + 1) % len(tour)]
                    self.pheromone[from_city][to_city] += pheromone_deposit
                    self.pheromone[to_city][from_city] += pheromone_deposit  # Symmetric

    def _check_convergence(self, best_distances_history: list[float], window_size: int = 5) -> bool:
        """检查算法是否收敛（基于最近几次迭代的改进幅度）
        
        Args:
            best_distances_history: 历史最佳距离记录
            window_size: 检查收敛的窗口大小
            
        Returns:
            bool: 如果算法收敛返回 True，否则返回 False
        """
        if len(best_distances_history) < window_size * 2:
            return False
            
        # 比较最近window_size次与之前window_size次的平均值
        recent_avg = sum(best_distances_history[-window_size:]) / window_size
        previous_avg = sum(best_distances_history[-(window_size*2):-window_size]) / window_size
        
        improvement_rate = abs(previous_avg - recent_avg) / previous_avg
        return improvement_rate < self.convergence_threshold

    def solveTSP(self) -> list[int]:
        """Solve the TSP using Ant Colony Optimization algorithm with convergence detection.

        Returns:
            list[int]: A list of city indices representing the best tour found.
        """
        best_tour = []
        best_distance = float('inf')
        previous_best_distance = float('inf')
        
        # 收敛检测变量
        no_improvement_count = 0
        best_distances_history = []
        
        for iteration in range(self.num_iterations):
            # Construct tours for all ants
            ant_tours = []
            ant_distances = []

            for ant in range(self.num_ants):
                tour = self._construct_ant_tour()
                distance = self.calculate_tour_distance(tour)
                ant_tours.append(tour)
                ant_distances.append(distance)

                # Update best solution
                if distance < best_distance:
                    best_tour = tour.copy()
                    best_distance = distance

            # Update pheromones
            self._update_pheromones(ant_tours, ant_distances)
            
            # 记录当前迭代的最佳距离
            best_distances_history.append(best_distance)
            
            # 检查是否有改进
            improvement = previous_best_distance - best_distance
            if improvement < self.convergence_threshold:
                no_improvement_count += 1
            else:
                no_improvement_count = 0  # 重置计数器
                
            previous_best_distance = best_distance
            
            # 收敛检测：如果连续多次迭代没有显著改进，则提前终止
            if no_improvement_count >= self.patience:
                print(f"算法在第 {iteration + 1} 次迭代后收敛，提前终止")
                print(f"连续 {self.patience} 次迭代改进小于阈值 {self.convergence_threshold}")
                break
            
            # Optional: Print progress
            if iteration % 10 == 0:
                print(f"迭代 {iteration}: 最佳距离 = {best_distance:.2f}, 改进 = {improvement:.6f}")
        
        # 如果是正常结束（达到最大迭代次数）
        if no_improvement_count < self.patience:
            print(f"算法达到最大迭代次数 {self.num_iterations} 后结束")
        
        # 输出收敛统计信息
        total_iterations = min(iteration + 1, self.num_iterations)
        print(f"总迭代次数: {total_iterations}")
        print(f"最终最佳距离: {best_distance:.2f}")
        
        # 计算收敛率（后期改进幅度）
        if len(best_distances_history) >= 10:
            early_avg = sum(best_distances_history[:10]) / 10
            late_avg = sum(best_distances_history[-10:]) / 10
            # 防止除零错误
            if early_avg > 0:
                improvement_rate = (early_avg - late_avg) / early_avg * 100
                print(f"收敛改进率: {improvement_rate:.2f}%")
            else:
                print("收敛改进率: 无法计算（初始距离为0）")

        return best_tour
def main():
    """Example usage of both TSP solvers."""
    # Example distance matrix for 4 cities
    # Cities: A(0), B(1), C(2), D(3)
    distance_matrix = RandomDistanceMatrixFactory(dimension=4, min_distance=1, max_distance=10).create_distance_matrix()
    time_manager = TimerManager()
    print("=== TSP Solver Comparison ===\n")

    # Test Simulated Annealing
    print("1. Simulated Annealing Algorithm:")
    print("-" * 40)
    sa_solver = SimulatedAnnealingTSPSolver(
        distance_matrix=distance_matrix,
        initial_temperature=1000.0,
        min_temperature=0.01,
        cooling_rate=0.995,
        max_iterations=10000,
    )

    with time_manager.create_timer("Simulated Annealing TSP"):
        sa_best_tour = sa_solver.solveTSP()
    sa_best_distance = sa_solver.calculate_tour_distance(sa_best_tour)

    print(f"Best tour found: {sa_best_tour}")
    print(f"Total distance: {sa_best_distance}")

    # Show the tour path
    city_names = ["A", "B", "C", "D"]
    sa_tour_path = " -> ".join([city_names[i] for i in sa_best_tour])
    sa_tour_path += f" -> {city_names[sa_best_tour[0]]}"  # Return to start
    print(f"Tour path: {sa_tour_path}\n")

    # Test Ant Colony Optimization
    print("2. Ant Colony Optimization Algorithm:")
    print("-" * 40)
    aco_solver = AntColonyOptimizationTSPSolver(
        distance_matrix=distance_matrix,
        num_ants=10,
        num_iterations=50,
        alpha=1.0,
        beta=2.0,
        evaporation_rate=0.5,
        Q=100.0,
    )

    with time_manager.create_timer("Ant Colony Optimization TSP"):
        aco_best_tour = aco_solver.solveTSP()
    aco_best_distance = aco_solver.calculate_tour_distance(aco_best_tour)

    print(f"\nFinal Results:")
    print(f"Best tour found: {aco_best_tour}")
    print(f"Total distance: {aco_best_distance}")

    aco_tour_path = " -> ".join([city_names[i] for i in aco_best_tour])
    aco_tour_path += f" -> {city_names[aco_best_tour[0]]}"  # Return to start
    print(f"Tour path: {aco_tour_path}\n")

    # Compare results
    print("=== Comparison ===")
    print(f"Simulated Annealing: {sa_best_distance:.2f}")
    print(f"Ant Colony Optimization: {aco_best_distance:.2f}")
    
    if sa_best_distance < aco_best_distance:
        print("Simulated Annealing found a better solution!")
    elif aco_best_distance < sa_best_distance:
        print("Ant Colony Optimization found a better solution!")
    else:
        print("Both algorithms found solutions with the same distance!")

    time_manager.print_summary()

if __name__ == "__main__":
    main()
