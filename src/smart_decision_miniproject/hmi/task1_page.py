from nicegui import ui
import plotly.graph_objects as go
import asyncio

from smart_decision_miniproject.solver.TSP import (
    SimulatedAnnealingTSPSolver,
    AntColonyOptimizationTSPSolver,
)

from smart_decision_miniproject.TSP_datamodel.distance_matrix_factory import (
    RandomDistanceMatrixFactory,
)

from smart_decision_miniproject.timer import TimerManager,Timer

# 算法参数配置字典
sa_params = {
    "initial_temperature": 1000,
    "min_temperature": 0.01,
    "cooling_rate": 0.95,
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

# 测试规模配置字典
scale_params = {"max_scale": 200, "scale_interval": 50}

# 全局UI组件变量
progress_bar = None
progress_label = None
time_chart_container = None
quality_chart_container = None
results_table_container = None

# 计算状态变量
is_running = False
sa_time_records = []
aco_time_records = []
sa_best_distances = []
aco_best_distances = []


def render_algorithm_comparison_content():
    """渲染算法比较页面内容"""
    global progress_bar, progress_label, time_chart_container, quality_chart_container, results_table_container
    
    # 主容器，居中并限制最大宽度
    with ui.column().classes("w-full max-w-6xl mx-auto q-px-md"):
        # 页面标题
        ui.label("Comparaison d'Algorithmes TSP").classes(
            "text-h3 text-center q-mt-lg q-mb-xl text-primary"
        )

        # 第一个区域：算法参数配置
        with ui.card().classes("w-full q-mb-xl shadow-lg q-pa-lg"):
            ui.label("⚙️ Configuration des Paramètres d'Algorithmes").classes(
                "text-h5 text-primary q-mb-lg text-center"
            )

            with ui.row().classes("w-full q-gutter-xl justify-center"):
                # 左列：Simulated Annealing 参数
                with ui.card().classes("flex-1 max-w-md q-pa-lg bg-green-1"):
                    ui.label("🔥 Recuit Simulé (SA)").classes(
                        "text-h6 text-center q-mb-lg text-green-8 text-weight-bold"
                    )

                    with ui.column().classes("q-gutter-md"):
                        ui.label("Température Initiale").classes(
                            "text-subtitle2 text-weight-medium q-mb-xs"
                        )
                        ui.number(
                            value=sa_params["initial_temperature"],
                            on_change=lambda e: sa_params.update(
                                {"initial_temperature": e.value}
                            ),
                        ).classes("q-mb-sm").props("outlined dense color=green-6")

                        ui.label("Température Minimale").classes(
                            "text-subtitle2 text-weight-medium q-mb-xs"
                        )
                        ui.number(
                            value=sa_params["min_temperature"],
                            min=0.01,
                            on_change=lambda e: sa_params.update(
                                {"min_temperature": e.value}
                            ),
                        ).classes("q-mb-sm").props("outlined dense color=green-6")

                        ui.label("Taux de Refroidissement").classes(
                            "text-subtitle2 text-weight-medium q-mb-xs"
                        )
                        ui.number(
                            value=sa_params["cooling_rate"],
                            step=0.01,
                            min=0.01,
                            max=0.99,
                            on_change=lambda e: sa_params.update(
                                {"cooling_rate": e.value}
                            ),
                        ).classes("q-mb-sm").props("outlined dense color=green-6")

                        ui.label("Itérations Maximum").classes(
                            "text-subtitle2 text-weight-medium q-mb-xs"
                        )
                        ui.number(
                            value=sa_params["max_iterations"],
                            min=100,
                            on_change=lambda e: sa_params.update(
                                {"max_iterations": e.value}
                            ),
                        ).classes("q-mb-sm").props("outlined dense color=green-6")

                # 右列：Ant Colony Optimization 参数
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

        # 第二个区域：测试规模配置
        with ui.card().classes("w-full q-mb-xl shadow-lg q-pa-lg"):
            ui.label("📊 Configuration de Test").classes(
                "text-h5 text-primary q-mb-lg text-center"
            )

            with ui.row().classes("w-full justify-center q-gutter-xl"):
                with ui.card().classes("flex-1 max-w-xs q-pa-lg bg-grey-1"):
                    with ui.column().classes("items-center q-gutter-md"):
                        ui.icon("trending_up", size="3em").classes("text-primary")
                        ui.label("Échelle Maximum").classes(
                            "text-subtitle1 text-weight-medium text-center"
                        )
                        ui.number(
                            value=scale_params["max_scale"],
                            min=50,
                            step=50,
                            on_change=lambda e: scale_params.update(
                                {"max_scale": e.value}
                            ),
                        ).classes("text-center").props("outlined dense color=primary")

                with ui.card().classes("flex-1 max-w-xs q-pa-lg bg-grey-1"):
                    with ui.column().classes("items-center q-gutter-md"):
                        ui.icon("linear_scale", size="3em").classes("text-primary")
                        ui.label("Intervalle d'Échelle").classes(
                            "text-subtitle1 text-weight-medium text-center"
                        )
                        ui.number(
                            value=scale_params["scale_interval"],
                            min=10,
                            step=10,
                            on_change=lambda e: scale_params.update(
                                {"scale_interval": e.value}
                            ),
                        ).classes("text-center").props("outlined dense color=primary")

        # 第三个区域：控制和进度
        with ui.card().classes("w-full q-mb-xl shadow-lg q-pa-lg"):
            ui.label("🎮 Contrôle d'Exécution").classes(
                "text-h5 text-primary q-mb-lg text-center"
            )

            # 控制按钮区域
            with ui.row().classes("w-full justify-center q-gutter-lg q-mb-lg"):
                ui.button(
                    "Lancer Comparaison",
                    icon="play_arrow",
                    on_click=lambda: start_comparison(),
                ).props("color=positive size=lg unelevated").classes("q-px-xl")

                ui.button(
                    "Arrêter", icon="stop", on_click=lambda: stop_comparison()
                ).props("color=negative size=lg outline").classes("q-px-xl")

                ui.button(
                    "Réinitialiser", icon="refresh", on_click=lambda: reset_comparison()
                ).props("color=grey size=lg outline").classes("q-px-xl")

            # 进度区域
            with ui.card().classes("w-full bg-grey-2 q-pa-lg"):
                ui.label("Progression").classes(
                    "text-h6 text-center q-mb-md text-weight-medium"
                )
                with ui.row().classes("w-full items-center q-gutter-md"):
                    ui.icon("timeline").classes("text-primary")
                    progress_bar = (
                        ui.linear_progress(value=0)
                        .classes("flex-1")
                        .props("size=md color=primary")
                    )
                    progress_label = ui.label("0%").classes(
                        "text-subtitle1 text-weight-bold text-primary"
                    )

        # 第四个区域：结果展示
        with ui.card().classes("w-full shadow-lg q-pa-lg"):
            ui.label("📈 Résultats de Comparaison").classes(
                "text-h5 text-primary q-mb-lg text-center"
            )

            # 结果图表容器
            with ui.row().classes("w-full q-gutter-lg q-mb-lg"):
                # 时间对比图表
                with ui.card().classes("flex-1 q-pa-md shadow-md"):
                    ui.label("⏱️ Temps d'Exécution").classes(
                        "text-h6 text-center q-mb-md text-weight-medium text-primary"
                    )
                    time_chart_container = ui.column().classes(
                        "w-full bg-gradient-to-r from-blue-50 to-green-50 rounded-borders border overflow-hidden"
                    )
                    with time_chart_container:
                        with ui.column().classes("items-center justify-center h-full q-pa-lg"):
                            ui.icon("schedule", size="4em").classes("text-grey-5")
                            ui.label("Graphique des temps d'exécution").classes(
                                "text-center text-grey-6"
                            )

                # 质量对比图表
                with ui.card().classes("flex-1 q-pa-md shadow-md"):
                    ui.label("🎯 Qualité des Solutions").classes(
                        "text-h6 text-center q-mb-md text-weight-medium text-primary"
                    )
                    quality_chart_container = ui.column().classes(
                        "w-full bg-gradient-to-r from-orange-50 to-red-50 rounded-borders border overflow-hidden"
                    )
                    with quality_chart_container:
                        with ui.column().classes("items-center justify-center h-full q-pa-lg"):
                            ui.icon("emoji_events", size="4em").classes("text-grey-5")
                            ui.label("Graphique de la qualité des solutions").classes(
                                "text-center text-grey-6"
                            )

            # 统计结果表格
            with ui.card().classes("w-full bg-grey-1 q-pa-lg"):
                ui.label("📋 Tableau Récapitulatif").classes(
                    "text-h6 q-mb-md text-center text-weight-medium"
                )
                results_table_container = ui.column().classes("w-full")
                with results_table_container:
                    with ui.column().classes("items-center justify-center q-pa-xl"):
                        ui.icon("table_chart", size="4em").classes("text-grey-5")
                        ui.label(
                            "Les résultats apparaîtront ici après l'exécution"
                        ).classes("text-center text-grey-6")


def update_progress(value, text):
    """更新进度条和标签"""
    global progress_bar, progress_label
    if progress_bar and progress_label:
        progress_bar.value = value / 100
        progress_label.text = f"{value:.1f}%"
        ui.update()

def create_time_chart(sa_times, aco_times, scales):
    """创建时间性能图表"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=scales,
        y=sa_times,
        mode='lines+markers',
        name='Recuit Simulé (SA)',
        line=dict(color='#27ae60', width=3, shape='spline'),
        marker=dict(size=8, color='#27ae60', symbol='circle'),
        hovertemplate='<b>SA</b><br>Taille: %{x}<br>Temps: %{y:.3f}s<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=scales,
        y=aco_times,
        mode='lines+markers',
        name='Colonies de Fourmis (ACO)',
        line=dict(color='#3498db', width=3, shape='spline'),
        marker=dict(size=8, color='#3498db', symbol='diamond'),
        hovertemplate='<b>ACO</b><br>Taille: %{x}<br>Temps: %{y:.3f}s<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text="Comparaison des Temps d'Exécution",
            font=dict(size=16, color="#2c3e50"),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=dict(text="Taille du Problème", font=dict(size=14, color="#34495e")),
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

def create_quality_chart(sa_distances, aco_distances, scales):
    """创建优化质量图表"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=scales,
        y=sa_distances,
        mode='lines+markers',
        name='Recuit Simulé (SA)',
        line=dict(color='#27ae60', width=3, shape='spline'),
        marker=dict(size=8, color='#27ae60', symbol='circle'),
        hovertemplate='<b>SA</b><br>Taille: %{x}<br>Distance: %{y:.2f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=scales,
        y=aco_distances,
        mode='lines+markers',
        name='Colonies de Fourmis (ACO)',
        line=dict(color='#3498db', width=3, shape='spline'),
        marker=dict(size=8, color='#3498db', symbol='diamond'),
        hovertemplate='<b>ACO</b><br>Taille: %{x}<br>Distance: %{y:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text="Comparaison de la Qualité des Solutions",
            font=dict(size=16, color="#2c3e50"),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=dict(text="Taille du Problème", font=dict(size=14, color="#34495e")),
            tickfont=dict(size=12, color="#34495e"),
            gridcolor="#ecf0f1"
        ),
        yaxis=dict(
            title=dict(text="Distance Totale", font=dict(size=14, color="#34495e")),
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
        
    scales = list(range(scale_params["scale_interval"], 
                       len(sa_time_records) * scale_params["scale_interval"] + 1, 
                       scale_params["scale_interval"]))
    
    # 清空并更新时间图表
    if time_chart_container:
        time_chart_container.clear()
        with time_chart_container:
            create_time_chart(sa_time_records, aco_time_records, scales)
    
    # 清空并更新质量图表
    if quality_chart_container:
        quality_chart_container.clear()
        with quality_chart_container:
            create_quality_chart(sa_best_distances, aco_best_distances, scales)

async def start_comparison():
    """启动算法比较 - 异步函数支持UI更新"""
    global is_running, sa_time_records, aco_time_records, sa_best_distances, aco_best_distances
    
    if is_running:
        return
        
    is_running = True
    print(f"Démarrage de la comparaison avec SA params: {sa_params}")
    print(f"ACO params: {aco_params}")
    print(f"Scale params: {scale_params}")

    # 重置数据
    sa_time_records.clear()
    aco_time_records.clear()
    sa_best_distances.clear()
    aco_best_distances.clear()
    
    update_progress(0, "0%")

    sa_timer_manager = TimerManager()
    aco_timer_manager = TimerManager()

    sa_solver = SimulatedAnnealingTSPSolver(
        initial_temperature=sa_params["initial_temperature"],
        min_temperature=sa_params["min_temperature"],
        cooling_rate=sa_params["cooling_rate"],
        max_iterations=sa_params["max_iterations"],
    )
    aco_solver = AntColonyOptimizationTSPSolver(
        num_ants=aco_params["num_ants"],
        alpha=aco_params["alpha"],
        beta=aco_params["beta"],
        evaporation_rate=aco_params["evaporation_rate"],
        Q=aco_params.get("Q", 100.0),
        convergence_threshold=aco_params.get("convergence_threshold", 1e-6),
        patience=aco_params.get("patience", 10),
        num_iterations=aco_params["num_iterations"],
    )

    total_steps = int(scale_params["max_scale"]) // int(scale_params["scale_interval"])
    current_step = 0

    for dim in range(
        int(scale_params["scale_interval"]),
        int(scale_params["max_scale"]) + 1,
        int(scale_params["scale_interval"]),
    ):
        if not is_running:  # 检查是否被停止
            break
            
        print(f"\n=== Test pour la taille: {dim} ===")
        distance_matrix = RandomDistanceMatrixFactory(
            dimension=dim, min_distance=10, max_distance=100
        ).create_distance_matrix()
        
        sa_solver.update_distance_matrix(distance_matrix)
        aco_solver.update_distance_matrix(distance_matrix)
        
        with sa_timer_manager.create_timer(str(dim)):
            sa_result = sa_solver.solveTSP()
        with aco_timer_manager.create_timer(str(dim)):
            aco_result = aco_solver.solveTSP()

        print(f"SA结果: {sa_result}")
        print(f"ACO结果: {aco_result}")
        
        sa_best_distance = distance_matrix.cal_tour_distance(sa_result)
        sa_best_distances.append(sa_best_distance)
        aco_best_distance = distance_matrix.cal_tour_distance(aco_result)
        aco_best_distances.append(aco_best_distance)
        
        print(f"SA距离: {sa_best_distance}, ACO距离: {aco_best_distance}")
        
        # 更新时间记录
        sa_time_records.append(sa_timer_manager.timers[str(dim)].elapsed_time)
        aco_time_records.append(aco_timer_manager.timers[str(dim)].elapsed_time)
        
        current_step += 1
        progress = (current_step / total_steps) * 100
        update_progress(progress, f"{progress:.1f}%")
        
        # 更新图表
        update_charts()
        
        # 给UI时间更新
        await asyncio.sleep(0.1)

    is_running = False
    print("Comparaison terminée!")
    update_progress(100, "100% - Terminé")


def stop_comparison():
    """停止算法比较 - 框架函数"""
    global is_running
    is_running = False
    print("Arrêt de la comparaison")


def reset_comparison():
    """重置比较结果 - 框架函数"""
    global sa_time_records, aco_time_records, sa_best_distances, aco_best_distances
    global time_chart_container, quality_chart_container
    
    print("Réinitialisation de la comparaison")
    
    # 重置数据
    sa_time_records.clear()
    aco_time_records.clear()
    sa_best_distances.clear()
    aco_best_distances.clear()
    
    # 重置进度
    update_progress(0, "0%")
    
    # 清空图表
    if time_chart_container:
        time_chart_container.clear()
        with time_chart_container:
            with ui.column().classes("items-center justify-center h-full"):
                ui.icon("schedule", size="4em").classes("text-grey-5")
                ui.label("Graphique des temps d'exécution").classes("text-center text-grey-6")
    
    if quality_chart_container:
        quality_chart_container.clear()
        with quality_chart_container:
            with ui.column().classes("items-center justify-center h-full"):
                ui.icon("emoji_events", size="4em").classes("text-grey-5")
                ui.label("Graphique de la qualité des solutions").classes("text-center text-grey-6")