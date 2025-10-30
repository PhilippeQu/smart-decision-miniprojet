import asyncio
from nicegui import ui
import plotly.graph_objects as go

from smart_decision_miniproject.solver.TSP import (
    SimulatedAnnealingTSPSolver,
    AntColonyOptimizationTSPSolver,
)
from smart_decision_miniproject.TSP_datamodel.distance_matrix_factory import (
    ChineseCityDistanceMatrixFactory,
)
from smart_decision_miniproject.timer import TimerManager

# 算法参数配置字典
sa_params = {
    "initial_temperature": 1000.0,
    "min_temperature": 0.01,
    "cooling_rate": 0.995,
    "max_iterations": 10000,
}

aco_params = {
    "num_ants": 10,
    "alpha": 1.0,
    "beta": 2.0,
    "evaporation_rate": 0.5,
    "Q": 100.0,
    "num_iterations": 100,
    "convergence_threshold": 1e-6,
    "patience": 10,
}

# 全局UI组件变量
progress_bar = None
progress_label = None
time_chart_container = None
quality_chart_container = None
results_table_container = None
sa_map_container = None
aco_map_container = None

# 计算状态变量
is_running = False
sa_time_records = []
aco_time_records = []
sa_best_distances = []
aco_best_distances = []

# 可选择的地点列表 - 中国主要城市
available_locations = [
    '北京',
    '上海', 
    '广州',
    '深圳',
    '天津',
    '重庆',
    '杭州',
    '南京',
    '武汉',
    '成都',
    '西安',
    '沈阳',
    '青岛',
    '大连',
    '厦门',
    '苏州',
    '宁波',
    '无锡',
    '长沙',
    '昆明'
]

# 已选择的地点
selected_locations = []


def update_progress(value, text):
    """更新进度条和标签"""
    global progress_bar, progress_label
    if progress_bar and progress_label:
        progress_bar.value = value / 100
        progress_label.text = f"{value:.1f}%"
        ui.update()


def create_time_chart(sa_times, aco_times, locations_count):
    """创建时间性能图表"""
    fig = go.Figure()
    
    x_values = [f"{i+3} villes" for i in range(len(sa_times))]
    
    fig.add_trace(go.Scatter(
        x=x_values,
        y=sa_times,
        mode='lines+markers',
        name='Recuit Simulé (SA)',
        line=dict(color='#27ae60', width=3, shape='spline'),
        marker=dict(size=8, color='#27ae60', symbol='circle'),
        hovertemplate='<b>SA</b><br>Villes: %{x}<br>Temps: %{y:.3f}s<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=x_values,
        y=aco_times,
        mode='lines+markers',
        name='Colonies de Fourmis (ACO)',
        line=dict(color='#3498db', width=3, shape='spline'),
        marker=dict(size=8, color='#3498db', symbol='diamond'),
        hovertemplate='<b>ACO</b><br>Villes: %{x}<br>Temps: %{y:.3f}s<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text="Comparaison des Temps d'Exécution",
            font=dict(size=16, color="#2c3e50"),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=dict(text="Nombre de Villes", font=dict(size=14, color="#34495e")),
            tickfont=dict(size=12, color="#34495e"),
            gridcolor="#ecf0f1"
        ),
        yaxis=dict(
            title=dict(text="Temps (secondes)", font=dict(size=14, color="#34495e")),
            tickfont=dict(size=12, color="#34495e"),
            gridcolor="#ecf0f1"
        ),
        template="plotly_white",
        height=350,
        margin=dict(l=60, r=20, t=60, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12)
        ),
        plot_bgcolor='rgba(248,249,250,0.8)',
        paper_bgcolor='rgba(255,255,255,0.9)'
    )
    
    return ui.plotly(fig).classes('w-full').style('min-height: 350px; max-height: 400px;')


def create_quality_chart(sa_distances, aco_distances, locations_count):
    """创建优化质量图表"""
    fig = go.Figure()
    
    x_values = [f"{i+3} villes" for i in range(len(sa_distances))]
    
    fig.add_trace(go.Scatter(
        x=x_values,
        y=sa_distances,
        mode='lines+markers',
        name='Recuit Simulé (SA)',
        line=dict(color='#27ae60', width=3, shape='spline'),
        marker=dict(size=8, color='#27ae60', symbol='circle'),
        hovertemplate='<b>SA</b><br>Villes: %{x}<br>Distance: %{y:.2f} km<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=x_values,
        y=aco_distances,
        mode='lines+markers',
        name='Colonies de Fourmis (ACO)',
        line=dict(color='#3498db', width=3, shape='spline'),
        marker=dict(size=8, color='#3498db', symbol='diamond'),
        hovertemplate='<b>ACO</b><br>Villes: %{x}<br>Distance: %{y:.2f} km<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text="Comparaison de la Qualité des Solutions",
            font=dict(size=16, color="#2c3e50"),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=dict(text="Nombre de Villes", font=dict(size=14, color="#34495e")),
            tickfont=dict(size=12, color="#34495e"),
            gridcolor="#ecf0f1"
        ),
        yaxis=dict(
            title=dict(text="Distance Totale (km)", font=dict(size=14, color="#34495e")),
            tickfont=dict(size=12, color="#34495e"),
            gridcolor="#ecf0f1"
        ),
        template="plotly_white",
        height=350,
        margin=dict(l=60, r=20, t=60, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12)
        ),
        plot_bgcolor='rgba(248,249,250,0.8)',
        paper_bgcolor='rgba(255,255,255,0.9)'
    )
    
    return ui.plotly(fig).classes('w-full').style('min-height: 350px; max-height: 400px;')


def update_charts():
    """更新图表显示"""
    global time_chart_container, quality_chart_container
    global sa_time_records, aco_time_records, sa_best_distances, aco_best_distances
    
    if not sa_time_records or not aco_time_records:
        return
    
    # 清空并重新创建时间图表
    if time_chart_container is not None:
        time_chart_container.clear()
        with time_chart_container:
            create_time_chart(sa_time_records, aco_time_records, len(sa_time_records))
    
    # 清空并重新创建质量图表
    if quality_chart_container is not None:
        quality_chart_container.clear()
        with quality_chart_container:
            create_quality_chart(sa_best_distances, aco_best_distances, len(sa_best_distances))


async def start_optimization():
    """启动地理TSP优化"""
    global is_running, sa_time_records, aco_time_records, sa_best_distances, aco_best_distances
    
    # 检查是否选择了足够的地点
    if len(selected_locations) < 3:
        ui.notify("Veuillez sélectionner au moins 3 destinations", type="warning")
        return
    
    is_running = True
    
    # 清空之前的记录
    sa_time_records.clear()
    aco_time_records.clear()
    sa_best_distances.clear()
    aco_best_distances.clear()
    
    update_progress(0, "0%")
    
    print(f"Démarrage de l'optimisation géographique avec SA params: {sa_params}")
    print(f"ACO params: {aco_params}")
    print(f"Destinations sélectionnées: {selected_locations}")
    
    sa_timer_manager = TimerManager()
    aco_timer_manager = TimerManager()
    
    sa_solver = SimulatedAnnealingTSPSolver(
        initial_temperature=sa_params["initial_temperature"],
        min_temperature=sa_params["min_temperature"],
        cooling_rate=sa_params["cooling_rate"],
        max_iterations=int(sa_params["max_iterations"]),
    )
    aco_solver = AntColonyOptimizationTSPSolver(
        num_ants=int(aco_params["num_ants"]),
        alpha=aco_params["alpha"],
        beta=aco_params["beta"],
        evaporation_rate=aco_params["evaporation_rate"],
        Q=aco_params.get("Q", 100.0),
        convergence_threshold=aco_params.get("convergence_threshold", 1e-6),
        patience=int(aco_params.get("patience", 10)),
        num_iterations=int(aco_params["num_iterations"]),
    )
    
    # 从3个城市开始，逐步增加到所有选中的城市
    total_steps = len(selected_locations) - 2  # 从3个城市开始
    current_step = 0
    
    for num_cities in range(3, len(selected_locations) + 1):
        if not is_running:  # 检查是否被停止
            break
            
        current_cities = selected_locations[:num_cities]
        print(f"\n=== Test pour {num_cities} villes: {current_cities} ===")
        
        # 创建中国城市距离矩阵
        distance_matrix = ChineseCityDistanceMatrixFactory(
            site_name_list=current_cities
        ).create_distance_matrix()
        
        sa_solver.update_distance_matrix(distance_matrix)
        aco_solver.update_distance_matrix(distance_matrix)
        
        with sa_timer_manager.create_timer(str(num_cities)):
            sa_result = sa_solver.solveTSP()
        with aco_timer_manager.create_timer(str(num_cities)):
            aco_result = aco_solver.solveTSP()

        print(f"SA结果: {sa_result}")
        print(f"ACO结果: {aco_result}")
        
        sa_best_distance = distance_matrix.cal_tour_distance(sa_result)
        sa_best_distances.append(sa_best_distance)
        aco_best_distance = distance_matrix.cal_tour_distance(aco_result)
        aco_best_distances.append(aco_best_distance)
        
        print(f"SA距离: {sa_best_distance:.2f} km, ACO距离: {aco_best_distance:.2f} km")
        
        # 更新时间记录
        sa_time_records.append(sa_timer_manager.timers[str(num_cities)].elapsed_time)
        aco_time_records.append(aco_timer_manager.timers[str(num_cities)].elapsed_time)
        
        current_step += 1
        progress = (current_step / total_steps) * 100
        update_progress(progress, f"{progress:.1f}%")
        
        # 更新图表
        update_charts()
        
        # 给UI时间更新
        await asyncio.sleep(0.1)

    is_running = False
    print("Optimisation géographique terminée!")
    update_progress(100, "100% - Terminé")


def stop_optimization():
    """停止优化"""
    global is_running
    is_running = False
    print("Arrêt de l'optimisation")


def reset_optimization():
    """重置优化结果"""
    global sa_time_records, aco_time_records, sa_best_distances, aco_best_distances
    global time_chart_container, quality_chart_container
    
    sa_time_records.clear()
    aco_time_records.clear()
    sa_best_distances.clear()
    aco_best_distances.clear()
    
    # 清空图表容器
    if time_chart_container is not None:
        time_chart_container.clear()
        with time_chart_container:
            with ui.column().classes("items-center justify-center q-pa-xl"):
                ui.icon("schedule", size="4em").classes("text-grey-5")
                ui.label("Les performances temporelles apparaîtront ici").classes("text-center text-grey-6")
    
    if quality_chart_container is not None:
        quality_chart_container.clear()
        with quality_chart_container:
            with ui.column().classes("items-center justify-center q-pa-xl"):
                ui.icon("trending_up", size="4em").classes("text-grey-5")
                ui.label("La qualité des solutions apparaîtra ici").classes("text-center text-grey-6")
    
    update_progress(0, "0%")
    print("Réinitialisation de l'optimisation")

def render_parameter_optimization_content():
    """渲染参数优化页面内容"""
    global progress_bar, progress_label, time_chart_container, quality_chart_container, results_table_container
    
    # 主容器，居中并限制最大宽度
    with ui.column().classes('w-full max-w-6xl mx-auto q-px-md'):
        # 页面标题
        ui.label('Optimisation de Paramètres TSP').classes('text-h3 text-center q-mt-lg q-mb-xl text-primary')
        
        # 第一个区域：算法参数配置
        with ui.card().classes('w-full q-mb-xl shadow-lg q-pa-lg'):
            ui.label('⚙️ Configuration des Paramètres d\'Algorithmes').classes('text-h5 text-primary q-mb-lg text-center')
            
            with ui.row().classes('w-full q-gutter-xl justify-center'):
                # 左列：Simulated Annealing 参数
                with ui.card().classes('flex-1 max-w-md q-pa-lg bg-green-1'):
                    ui.label('🔥 Recuit Simulé (SA)').classes('text-h6 text-center q-mb-lg text-green-8 text-weight-bold')
                    
                    with ui.column().classes('q-gutter-md'):
                        ui.label('Température Initiale').classes('text-subtitle2 text-weight-medium q-mb-xs')
                        ui.number(
                            value=sa_params['initial_temperature'],
                            on_change=lambda e: sa_params.update({'initial_temperature': e.value})
                        ).classes('q-mb-sm').props('outlined dense color=green-6')
                        
                        ui.label('Taux de Refroidissement').classes('text-subtitle2 text-weight-medium q-mb-xs')
                        ui.number(
                            value=sa_params['cooling_rate'],
                            step=0.01,
                            min=0.01,
                            max=0.99,
                            on_change=lambda e: sa_params.update({'cooling_rate': e.value})
                        ).classes('q-mb-sm').props('outlined dense color=green-6')
                        
                        ui.label('Température Minimale').classes('text-subtitle2 text-weight-medium q-mb-xs')
                        ui.number(
                            value=sa_params['min_temperature'],
                            min=0.01,
                            on_change=lambda e: sa_params.update({'min_temperature': e.value})
                        ).classes('q-mb-sm').props('outlined dense color=green-6')
                        
                        ui.label('Itérations Maximum').classes('text-subtitle2 text-weight-medium q-mb-xs')
                        ui.number(
                            value=sa_params['max_iterations'],
                            min=100,
                            on_change=lambda e: sa_params.update({'max_iterations': e.value})
                        ).classes('q-mb-sm').props('outlined dense color=green-6')
                
                # 右列：Ant Colony Optimization 参数
                with ui.card().classes('flex-1 max-w-md q-pa-lg bg-blue-1'):
                    ui.label('🐜 Colonies de Fourmis (ACO)').classes('text-h6 text-center q-mb-lg text-blue-8 text-weight-bold')
                    
                    with ui.column().classes('q-gutter-md'):
                        ui.label('Nombre de Fourmis').classes('text-subtitle2 text-weight-medium q-mb-xs')
                        ui.number(
                            value=aco_params['num_ants'],
                            min=10,
                            on_change=lambda e: aco_params.update({'num_ants': e.value})
                        ).classes('q-mb-sm').props('outlined dense color=blue-6')
                        
                        ui.label('Alpha (Phéromone)').classes('text-subtitle2 text-weight-medium q-mb-xs')
                        ui.number(
                            value=aco_params['alpha'],
                            step=0.1,
                            min=0.1,
                            on_change=lambda e: aco_params.update({'alpha': e.value})
                        ).classes('q-mb-sm').props('outlined dense color=blue-6')
                        
                        ui.label('Beta (Distance)').classes('text-subtitle2 text-weight-medium q-mb-xs')
                        ui.number(
                            value=aco_params['beta'],
                            step=0.1,
                            min=0.1,
                            on_change=lambda e: aco_params.update({'beta': e.value})
                        ).classes('q-mb-sm').props('outlined dense color=blue-6')
                        
                        ui.label('Taux d\'Évaporation').classes('text-subtitle2 text-weight-medium q-mb-xs')
                        ui.number(
                            value=aco_params['evaporation_rate'],
                            step=0.1,
                            min=0.1,
                            max=0.9,
                            on_change=lambda e: aco_params.update({'evaporation_rate': e.value})
                        ).classes('q-mb-sm').props('outlined dense color=blue-6')
                        
                        ui.label('Itérations Maximum').classes('text-subtitle2 text-weight-medium q-mb-xs')
                        ui.number(
                            value=aco_params['num_iterations'],
                            min=100,
                            on_change=lambda e: aco_params.update({'num_iterations': e.value})
                        ).classes('q-mb-sm').props('outlined dense color=blue-6')
        
        # 第二个区域：地点选择区域
        with ui.card().classes('w-full q-mb-xl shadow-lg q-pa-lg'):
            ui.label('🗺️ Sélection des Destinations').classes('text-h5 text-primary q-mb-lg text-center')
            
            # 已选择地点的快速显示
            selected_display = ui.label('Aucune destination sélectionnée').classes('text-center text-grey-6 q-mb-lg')
            
            # 直接使用网格布局展示所有地点，无需滚动
            with ui.grid(columns=5).classes('w-full q-gutter-md q-mb-lg'):
                for location in available_locations:
                    with ui.card().classes('q-pa-lg hover-shadow cursor-pointer transition-all bg-gradient-to-br from-blue-50 to-indigo-50').props('flat bordered'):
                        with ui.column().classes('items-center q-gutter-md'):
                            # 地点图标容器
                            with ui.element('div').classes('q-pa-md rounded-full bg-blue-100 shadow-sm'):
                                ui.icon('location_on', size='2em').classes('text-blue-600')
                            
                            # 地点名称
                            ui.label(location).classes('text-subtitle1 text-center text-weight-bold text-grey-8')
                            
                            # 复选框区域
                            with ui.row().classes('w-full justify-center'):
                                checkbox = ui.checkbox(
                                    value=location in selected_locations,
                                    on_change=lambda e, loc=location: toggle_location_improved(loc, e.value, selected_display)
                                ).classes('q-mt-sm').props('color=blue-6 size=md')
            
            # 操作按钮区域
            with ui.row().classes('w-full justify-center q-gutter-lg q-mt-xl'):
                ui.button(
                    'Sélectionner Tout',
                    icon='check_circle_outline',
                    on_click=lambda: select_all_locations(selected_display)
                ).props('color=blue-6 size=lg unelevated').classes('q-px-xl q-py-md text-weight-bold')
                
                ui.button(
                    'Effacer Tout',
                    icon='highlight_off',
                    on_click=lambda: clear_all_locations(selected_display)
                ).props('color=red-6 size=lg outline').classes('q-px-xl q-py-md text-weight-bold')
        
        # 第三个区域：控制和进度
        with ui.card().classes('w-full q-mb-xl shadow-lg q-pa-lg'):
            ui.label('🎮 Contrôle d\'Exécution').classes('text-h5 text-primary q-mb-lg text-center')
            
            # 控制按钮区域
            with ui.row().classes('w-full justify-center q-gutter-lg q-mb-lg'):
                ui.button(
                    'Lancer Optimisation',
                    icon='play_arrow',
                    on_click=lambda: asyncio.create_task(start_optimization())
                ).props('color=positive size=lg unelevated').classes('q-px-xl')
                
                ui.button(
                    'Arrêter',
                    icon='stop',
                    on_click=lambda: stop_optimization()
                ).props('color=negative size=lg outline').classes('q-px-xl')
                
                ui.button(
                    'Réinitialiser',
                    icon='refresh',
                    on_click=lambda: reset_optimization()
                ).props('color=grey size=lg outline').classes('q-px-xl')
            
            # 进度区域
            with ui.card().classes('w-full bg-grey-2 q-pa-lg'):
                ui.label('Progression').classes('text-h6 text-center q-mb-md text-weight-medium')
                with ui.row().classes('w-full items-center q-gutter-md'):
                    ui.icon('timeline').classes('text-primary')
                    progress_bar = ui.linear_progress(value=0).classes('flex-1').props('size=md color=primary')
                    progress_label = ui.label('0%').classes('text-subtitle1 text-weight-bold text-primary')
        
        # 第四个区域：结果展示 - 性能图表
        with ui.card().classes('w-full shadow-lg q-pa-lg'):
            ui.label('� Résultats de Comparaison').classes('text-h5 text-primary q-mb-lg text-center')
            
            # 结果图表容器
            with ui.row().classes('w-full q-gutter-lg q-mb-lg'):
                # 时间性能图表
                with ui.card().classes('flex-1 q-pa-lg'):
                    ui.label('⏱️ Temps d\'Exécution').classes('text-h6 text-center q-mb-md text-weight-medium')
                    time_chart_container = ui.column().classes('w-full bg-gradient-to-r from-purple-50 to-indigo-50 rounded-borders border')
                    with time_chart_container:
                        with ui.column().classes('items-center justify-center q-pa-xl'):
                            ui.icon('schedule', size='4em').classes('text-grey-5')
                            ui.label('Les performances temporelles apparaîtront ici').classes('text-center text-grey-6')
                
                # 质量性能图表
                with ui.card().classes('flex-1 q-pa-lg'):
                    ui.label('🎯 Qualité des Solutions').classes('text-h6 text-center q-mb-md text-weight-medium')
                    quality_chart_container = ui.column().classes('w-full bg-gradient-to-r from-green-50 to-teal-50 rounded-borders border')
                    with quality_chart_container:
                        with ui.column().classes('items-center justify-center q-pa-xl'):
                            ui.icon('trending_up', size='4em').classes('text-grey-5')
                            ui.label('La qualité des solutions apparaîtra ici').classes('text-center text-grey-6')
            
            # 统计结果表格
            with ui.card().classes('w-full bg-grey-1 q-pa-lg'):
                ui.label('📊 Statistiques de Performance').classes('text-h6 q-mb-md text-center text-weight-medium')
                results_table_container = ui.column().classes('w-full')
                with results_table_container:
                    with ui.column().classes('items-center justify-center q-pa-xl'):
                        ui.icon('assessment', size='4em').classes('text-grey-5')
                        ui.label('Les statistiques de performance apparaîtront ici après l\'exécution').classes('text-center text-grey-6')

def toggle_location_improved(location, is_selected, selected_display):
    """改进的切换地点选择状态"""
    global selected_locations
    if is_selected and location not in selected_locations:
        selected_locations.append(location)
    elif not is_selected and location in selected_locations:
        selected_locations.remove(location)
    
    # 更新显示
    update_selected_display(selected_display)
    print(f"地点 {location} {'已选择' if is_selected else '已取消选择'}")
    print(f"当前选择的地点: {selected_locations}")

def update_selected_display(selected_display):
    """更新已选择地点的显示"""
    if selected_locations:
        locations_text = ', '.join(selected_locations)
        if len(locations_text) > 100:
            locations_text = locations_text[:97] + '...'
        selected_display.text = f'✅ Sélectionnées ({len(selected_locations)}): {locations_text}'
        selected_display.classes('text-center text-green-700 text-weight-bold q-px-md q-py-sm bg-green-50 rounded-borders border-l-4 border-green-500')
    else:
        selected_display.text = '🗺️ Aucune destination sélectionnée - Choisissez vos villes'
        selected_display.classes('text-center text-grey-600 q-px-md q-py-sm bg-grey-50 rounded-borders border-l-4 border-grey-300')

def select_all_locations(selected_display):
    """选择所有地点"""
    global selected_locations
    selected_locations = available_locations.copy()
    update_selected_display(selected_display)
    print("已选择所有地点")
    # 注意：在实际应用中，这里需要更新UI中所有复选框的状态

def clear_all_locations(selected_display):
    """清除所有选择的地点"""
    global selected_locations
    selected_locations.clear()
    update_selected_display(selected_display)
    print("已清除所有选择的地点")
    # 注意：在实际应用中，这里需要更新UI中所有复选框的状态

def toggle_location(location, is_selected):
    """切换地点选择状态（保留原函数以兼容）"""
    global selected_locations
    if is_selected and location not in selected_locations:
        selected_locations.append(location)
    elif not is_selected and location in selected_locations:
        selected_locations.remove(location)
    
    print(f"地点 {location} {'已选择' if is_selected else '已取消选择'}")
    print(f"当前选择的地点: {selected_locations}")

def remove_location(location):
    """移除选择的地点（保留原函数以兼容）"""
    global selected_locations
    if location in selected_locations:
        selected_locations.remove(location)
    print(f"移除地点: {location}")
    print(f"当前选择的地点: {selected_locations}")