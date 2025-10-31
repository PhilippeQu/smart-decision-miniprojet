import asyncio
from nicegui import ui
import plotly.graph_objects as go
import folium
import tempfile
import os
import math

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
    "initial_temperature": 1000,
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

    # 在优化完成后，使用最终结果更新地图
    if is_running and len(selected_locations) >= 3:
        # 创建最终的距离矩阵和求解器结果
        final_distance_matrix = ChineseCityDistanceMatrixFactory(
            site_name_list=selected_locations
        ).create_distance_matrix()
        
        sa_solver.update_distance_matrix(final_distance_matrix)
        aco_solver.update_distance_matrix(final_distance_matrix)
        
        final_sa_result = sa_solver.solveTSP()
        final_aco_result = aco_solver.solveTSP()
        
        # 更新地图显示
        update_map_display(final_sa_result, final_aco_result)

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
    global progress_bar, progress_label, time_chart_container, quality_chart_container, results_table_container, sa_map_container, aco_map_container
    
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
                        
                        ui.label('Température Minimale').classes('text-subtitle2 text-weight-medium q-mb-xs')
                        ui.number(
                            value=sa_params['min_temperature'],
                            min=0.01,
                            on_change=lambda e: sa_params.update({'min_temperature': e.value})
                        ).classes('q-mb-sm').props('outlined dense color=green-6')
                        
                        ui.label('Taux de Refroidissement').classes('text-subtitle2 text-weight-medium q-mb-xs')
                        ui.number(
                            value=sa_params['cooling_rate'],
                            step=0.01,
                            min=0.01,
                            max=0.99,
                            on_change=lambda e: sa_params.update({'cooling_rate': e.value})
                        ).classes('q-mb-sm').props('outlined dense color=green-6')
                        
                        ui.label('Itérations Maximum').classes('text-subtitle2 text-weight-medium q-mb-xs')
                        ui.number(
                            value=sa_params['max_iterations'],
                            min=100,
                            on_change=lambda e: sa_params.update({'max_iterations': e.value})
                        ).classes('q-mb-sm').props('outlined dense color=green-6')
                
                with ui.card().classes("flex-1 max-w-md q-pa-lg bg-blue-1"):
                    ui.label("🐜 Colonies de Fourmis (ACO)").classes(
                        "text-h6 text-center q-mb-lg text-blue-8 text-weight-bold"
                    )

                    # 使用两列布局来容纳更多参数
                    with ui.row().classes("w-full q-gutter-md"):
                        # 左列参数
                        with ui.column().classes("flex-1 q-gutter-md"):
                            ui.label("Nombre de Fourmis").classes(
                                "text-subtitle2 text-weight-medium q-mb-xs"
                            )
                            ui.number(
                                value=aco_params["num_ants"],
                                min=10,
                                on_change=lambda e: aco_params.update(
                                    {"num_ants": e.value}
                                ),
                            ).classes("q-mb-sm").props("outlined dense color=blue-6")

                            ui.label("Alpha (Phéromone)").classes(
                                "text-subtitle2 text-weight-medium q-mb-xs"
                            )
                            ui.number(
                                value=aco_params["alpha"],
                                step=0.1,
                                min=0.1,
                                on_change=lambda e: aco_params.update(
                                    {"alpha": e.value}
                                ),
                            ).classes("q-mb-sm").props("outlined dense color=blue-6")

                            ui.label("Beta (Distance)").classes(
                                "text-subtitle2 text-weight-medium q-mb-xs"
                            )
                            ui.number(
                                value=aco_params["beta"],
                                step=0.1,
                                min=0.1,
                                on_change=lambda e: aco_params.update(
                                    {"beta": e.value}
                                ),
                            ).classes("q-mb-sm").props("outlined dense color=blue-6")

                            ui.label("Taux d'Évaporation").classes(
                                "text-subtitle2 text-weight-medium q-mb-xs"
                            )
                            ui.number(
                                value=aco_params["evaporation_rate"],
                                step=0.1,
                                min=0.1,
                                max=0.9,
                                on_change=lambda e: aco_params.update(
                                    {"evaporation_rate": e.value}
                                ),
                            ).classes("q-mb-sm").props("outlined dense color=blue-6")

                        # 右列参数
                        with ui.column().classes("flex-1 q-gutter-md"):
                            ui.label("Q (Constante de renforcement)").classes(
                                "text-subtitle2 text-weight-medium q-mb-xs"
                            )
                            ui.number(
                                value=aco_params.get("Q", 100.0),
                                step=1.0,
                                min=0.0,
                                on_change=lambda e: aco_params.update({"Q": e.value}),
                            ).classes("q-mb-sm").props("outlined dense color=blue-6")

                            ui.label("Seuil de Convergence").classes(
                                "text-subtitle2 text-weight-medium q-mb-xs"
                            )
                            ui.number(
                                value=aco_params.get("convergence_threshold", 1e-6),
                                step=1e-6,
                                min=0.0,
                                on_change=lambda e: aco_params.update(
                                    {"convergence_threshold": e.value}
                                ),
                            ).classes("q-mb-sm").props("outlined dense color=blue-6")

                            ui.label("Patience (itérations sans amélioration)").classes(
                                "text-subtitle2 text-weight-medium q-mb-xs"
                            )
                            ui.number(
                                value=aco_params.get("patience", 10),
                                step=1,
                                min=0,
                                on_change=lambda e: aco_params.update(
                                    {
                                        "patience": (
                                            int(e.value)
                                            if e.value is not None
                                            else e.value
                                        )
                                    }
                                ),
                            ).classes("q-mb-sm").props("outlined dense color=blue-6")

                            ui.label("Itérations Maximum").classes(
                                "text-subtitle2 text-weight-medium q-mb-xs"
                            )
                            ui.number(
                                value=aco_params["num_iterations"],
                                min=100,
                                on_change=lambda e: aco_params.update(
                                    {"num_iterations": e.value}
                                ),
                            ).classes("q-mb-sm").props("outlined dense color=blue-6")
        
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
            
            # # 统计结果表格
            # with ui.card().classes('w-full bg-grey-1 q-pa-lg'):
            #     ui.label('📊 Statistiques de Performance').classes('text-h6 q-mb-md text-center text-weight-medium')
            #     results_table_container = ui.column().classes('w-full')
            #     with results_table_container:
            #         with ui.column().classes('items-center justify-center q-pa-xl'):
            #             ui.icon('assessment', size='4em').classes('text-grey-5')
            #             ui.label('Les statistiques de performance apparaîtront ici après l\'exécution').classes('text-center text-grey-6')
        
        # 第五个区域：地理地图显示
        with ui.card().classes('w-full shadow-lg q-pa-lg q-mt-xl'):
            ui.label('🗺️ Visualisation Géographique des Routes').classes('text-h5 text-primary q-mb-lg text-center')
            
            # 地图容器区域
            with ui.row().classes('w-full q-gutter-lg'):
                # SA地图容器
                with ui.card().classes('flex-1 q-pa-md').style('overflow: hidden;'):
                    global sa_map_container
                    sa_map_container = ui.column().classes('w-full').style('max-width: 100%;')
                    with sa_map_container:
                        with ui.column().classes('items-center justify-center q-pa-xl'):
                            ui.icon('map', size='4em').classes('text-red-5')
                            ui.label('🔥 La route du Recuit Simulé apparaîtra ici').classes('text-center text-grey-6')
                
                # ACO地图容器
                with ui.card().classes('flex-1 q-pa-md').style('overflow: hidden;'):
                    global aco_map_container
                    aco_map_container = ui.column().classes('w-full').style('max-width: 100%;')
                    with aco_map_container:
                        with ui.column().classes('items-center justify-center q-pa-xl'):
                            ui.icon('map', size='4em').classes('text-green-5')
                            ui.label('🐜 La route des Colonies de Fourmis apparaîtra ici').classes('text-center text-grey-6')
            
            # # 添加地图图例
            # with ui.card().classes('w-full bg-grey-50 q-pa-md q-mt-lg'):
            #     ui.label('🎯 Légende des Cartes').classes('text-h6 text-center q-mb-md text-weight-bold')
            #     with ui.row().classes('w-full justify-center q-gutter-lg'):
            #         with ui.column().classes('items-center'):
            #             ui.icon('play_arrow', size='2em').classes('text-green-600')
            #             ui.label('Point de Départ').classes('text-caption text-center')
                    
            #         with ui.column().classes('items-center'):
            #             ui.icon('location_on', size='2em').classes('text-blue-600')
            #             ui.label('Villes à Visiter').classes('text-caption text-center')
                    
            #         with ui.column().classes('items-center'):
            #             ui.html('<div style="width: 30px; height: 4px; background-color: red; border-radius: 2px;"></div>', sanitize=False)
            #             ui.label('Route SA').classes('text-caption text-center')
                    
            #         with ui.column().classes('items-center'):
            #             ui.html('<div style="width: 30px; height: 4px; background-color: green; border-radius: 2px;"></div>', sanitize=False)
            #             ui.label('Route ACO').classes('text-caption text-center')

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


def create_route_map(locations, route, algorithm_name, color='blue'):
    """创建显示路径的地理地图"""
    if not locations or not route:
        return None
    
    # 中国主要城市坐标字典
    city_coords = {
        '北京': (39.9042, 116.4074),
        '上海': (31.2304, 121.4737),
        '广州': (23.1291, 113.2644),
        '深圳': (22.5431, 114.0579),
        '天津': (39.3434, 117.3616),
        '重庆': (29.5630, 106.5516),
        '杭州': (30.2741, 120.1551),
        '南京': (32.0603, 118.7969),
        '武汉': (30.5928, 114.3055),
        '成都': (30.6720, 104.0633),
        '西安': (34.3416, 108.9398),
        '沈阳': (41.8057, 123.4315),
        '青岛': (36.0671, 120.3826),
        '大连': (38.9140, 121.6147),
        '厦门': (24.4798, 118.0819),
        '苏州': (31.2989, 120.5853),
        '宁波': (29.8683, 121.5440),
        '无锡': (31.4912, 120.3116),
        '长沙': (28.2282, 112.9388),
        '昆明': (25.0389, 102.7183)
    }
    
    # 计算地图中心点
    lats = [city_coords[city][0] for city in locations if city in city_coords]
    lons = [city_coords[city][1] for city in locations if city in city_coords]
    
    if not lats or not lons:
        return None
    
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    
    # 创建高质量地图
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=5,
        tiles=None,  # 不使用默认瓦片
        prefer_canvas=True,
        max_zoom=18,
        min_zoom=3
    )
    
    # 添加高质量地图瓦片
    folium.TileLayer(
        tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name='OpenStreetMap',
        overlay=False,
        control=True,
        opacity=0.9
    ).add_to(m)
    
    # 添加卫星图层作为备选
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # 添加城市标记（美化版）
    for i, city in enumerate(locations):
        if city in city_coords:
            lat, lon = city_coords[city]
            
            # 起点使用特殊图标
            if i == 0:
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(f"<div style='font-family: Arial; text-align: center;'><b>🏁 起点</b><br><span style='color: #2E8B57; font-weight: bold;'>{city}</span><br><small>编号: {i}</small></div>", max_width=200),
                    tooltip=f"🏁 起点: {city}",
                    icon=folium.Icon(
                        color='green', 
                        icon='play', 
                        prefix='fa',
                        icon_color='white'
                    )
                ).add_to(m)
            else:
                # 其他城市使用数字标记 - 使用基本图标
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(f"<div style='font-family: Arial; text-align: center;'><b>📍 城市</b><br><span style='color: #4169E1; font-weight: bold;'>{city}</span><br><small>编号: {i}</small></div>", max_width=200),
                    tooltip=f"📍 {city} (#{i})",
                    icon=folium.Icon(
                        color='blue',
                        icon='info-sign',
                        prefix='glyphicon'
                    )
                ).add_to(m)
    
    # 添加美化的路径线
    if len(route) > 1:
        route_coords = []
        for city_idx in route:
            if city_idx < len(locations):
                city = locations[city_idx]
                if city in city_coords:
                    route_coords.append(city_coords[city])
        
        if len(route_coords) > 1:
            # 主路径线
            folium.PolyLine(
                route_coords,
                color=color,
                weight=4,
                opacity=0.8,
                popup=folium.Popup(f"<div style='font-family: Arial; text-align: center;'><b>🚗 {algorithm_name}</b><br><small>点击查看路径详情</small></div>", max_width=200),
                tooltip=f"🚗 Route {algorithm_name}"
            ).add_to(m)
            
            # 添加简化的路径方向标记
            for i in range(len(route_coords) - 1):
                start = route_coords[i]
                end = route_coords[i + 1]
                mid_lat = (start[0] + end[0]) / 2
                mid_lon = (start[1] + end[1]) / 2
                
                # 添加简单的圆形标记显示方向
                folium.CircleMarker(
                    [mid_lat, mid_lon],
                    radius=3,
                    popup=f"路段 {i+1}",
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.6
                ).add_to(m)
    
    # 添加图层控制
    folium.LayerControl().add_to(m)
    
    # 保存地图到临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
    m.save(temp_file.name)
    return temp_file.name


def update_map_display(sa_result=None, aco_result=None):
    """更新地图显示"""
    global sa_map_container, aco_map_container, selected_locations
    
    if not selected_locations:
        return
    
    # 更新SA地图
    if sa_result and sa_map_container is not None:
        sa_map_container.clear()
        # sa_result 是一个 list[int]，直接使用它作为路线
        with sa_map_container:
            with ui.card().classes('w-full'):
                ui.label('🔥 Route Recuit Simulé').classes('text-h6 text-center q-mb-md text-red-600')
                create_route_map_display(selected_locations, sa_result, "Recuit Simulé", '#FF4444')
    
    # 更新ACO地图
    if aco_result and aco_map_container is not None:
        aco_map_container.clear()
        # aco_result 是一个 list[int]，直接使用它作为路线
        with aco_map_container:
            with ui.card().classes('w-full'):
                ui.label('� Route Colonies de Fourmis').classes('text-h6 text-center q-mb-md text-green-600')
                create_route_map_display(selected_locations, aco_result, "Colonies de Fourmis", 'green')


def create_route_map_display(locations, route, algorithm_name, color='blue'):
    """直接在UI中创建和显示路径地图"""
    if not locations or not route:
        ui.label('Aucune route à afficher').classes('text-center text-grey-6')
        return
    
    # 中国主要城市坐标字典
    city_coords = {
        '北京': (39.9042, 116.4074),
        '上海': (31.2304, 121.4737),
        '广州': (23.1291, 113.2644),
        '深圳': (22.5431, 114.0579),
        '天津': (39.3434, 117.3616),
        '重庆': (29.5630, 106.5516),
        '杭州': (30.2741, 120.1551),
        '南京': (32.0603, 118.7969),
        '武汉': (30.5928, 114.3055),
        '成都': (30.6720, 104.0633),
        '西安': (34.3416, 108.9398),
        '沈阳': (41.8057, 123.4315),
        '青岛': (36.0671, 120.3826),
        '大连': (38.9140, 121.6147),
        '厦门': (24.4798, 118.0819),
        '苏州': (31.2989, 120.5853),
        '宁波': (29.8683, 121.5440),
        '无锡': (31.4912, 120.3116),
        '长沙': (28.2282, 112.9388),
        '昆明': (25.0389, 102.7183)
    }
    
    # 创建简化的地图HTML
    map_html = create_simple_map_html(locations, route, algorithm_name, color, city_coords)
    
    # 直接显示HTML内容，确保不超出卡片边界
    with ui.column().classes('w-full').style('max-width: 100%; box-sizing: border-box;'):
        ui.html(map_html, sanitize=False).style('height: 350px; width: 100%; max-width: 100%; overflow: hidden; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box;')


def create_simple_map_html(locations, route, algorithm_name, color, city_coords):
    """创建简化的SVG地图HTML"""
    
    # 获取有效的城市坐标
    valid_cities = [(city, city_coords[city]) for city in locations if city in city_coords]
    
    if not valid_cities:
        return '<div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #f5f5f5; border-radius: 8px;"><span style="color: #666;">Aucune ville valide trouvée</span></div>'
    
    # 计算SVG的边界
    lats = [coord[0] for _, coord in valid_cities]
    lons = [coord[1] for _, coord in valid_cities]
    
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    # 添加边距
    lat_margin = (max_lat - min_lat) * 0.1 or 0.1
    lon_margin = (max_lon - min_lon) * 0.1 or 0.1
    
    min_lat -= lat_margin
    max_lat += lat_margin
    min_lon -= lon_margin
    max_lon += lon_margin
    
    # SVG尺寸 - 使用百分比和viewBox来实现响应式
    svg_width = 100  # 将作为viewBox的宽度
    svg_height = 60  # 将作为viewBox的高度，保持合适的宽高比
    
    # 坐标转换函数
    def lat_to_y(lat):
        return svg_height - ((lat - min_lat) / (max_lat - min_lat)) * svg_height
    
    def lon_to_x(lon):
        return ((lon - min_lon) / (max_lon - min_lon)) * svg_width
    
    # 开始构建SVG - 使用viewBox实现响应式
    svg_content = f'''
    <svg viewBox="0 0 {svg_width} {svg_height}" style="width: 100%; height: 100%; background: #f8f9fa; border-radius: 8px;">
        <defs>
            <style>
                .city-circle {{ fill: #4285f4; stroke: white; stroke-width: 0.5; }}
                .start-city {{ fill: #34a853; }}
                .route-line {{ fill: none; stroke: {color}; stroke-width: 0.8; stroke-opacity: 0.8; }}
                .city-label {{ font-family: Arial, sans-serif; font-size: 2.5px; fill: #333; text-anchor: middle; }}
            </style>
        </defs>
        
        <!-- 背景网格 -->
        <defs>
            <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#e0e0e0" stroke-width="0.2" opacity="0.3"/>
            </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
    '''
    
    # 绘制路径线
    if len(route) > 1:
        route_coords = []
        for city_idx in route:
            if city_idx < len(locations):
                city = locations[city_idx]
                if city in city_coords:
                    lat, lon = city_coords[city]
                    x = lon_to_x(lon)
                    y = lat_to_y(lat)
                    route_coords.append((x, y))
        
        if len(route_coords) > 1:
            # 连接所有点形成路径
            path_d = f"M {route_coords[0][0]},{route_coords[0][1]}"
            for x, y in route_coords[1:]:
                path_d += f" L {x},{y}"
            # 回到起点
            path_d += f" L {route_coords[0][0]},{route_coords[0][1]}"
            
            svg_content += f'<path d="{path_d}" class="route-line" />'
    
    # 绘制城市点和标签
    for i, (city, (lat, lon)) in enumerate(valid_cities):
        x = lon_to_x(lon)
        y = lat_to_y(lat)
        
        # 起点用不同颜色
        circle_class = "city-circle start-city" if i == 0 else "city-circle"
        
        svg_content += f'''
            <circle cx="{x}" cy="{y}" r="1.5" class="{circle_class}" />
            <text x="{x}" y="{y-2}" class="city-label">{city}</text>
            <text x="{x}" y="{y+3.5}" class="city-label" style="font-size: 2px; fill: #666;">#{i}</text>
        '''
    
    svg_content += '</svg>'
    
    # 添加标题和路径信息
    route_info = " → ".join([f"{locations[i]}({i})" for i in route[:5]])  # 只显示前5个城市
    if len(route) > 5:
        route_info += f" ... (+{len(route)-5} villes)"
    
    html_content = f'''
    <div style="padding: 10px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h4 style="margin: 0 0 10px 0; color: {color}; text-align: center;">{algorithm_name}</h4>
        <div style="text-align: center; margin-bottom: 10px;">
            {svg_content}
        </div>
        <div style="font-size: 12px; color: #666; text-align: center; word-wrap: break-word;">
            <strong>Route:</strong> {route_info}
        </div>
    </div>
    '''
    
    return html_content