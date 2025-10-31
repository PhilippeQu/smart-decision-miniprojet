from nicegui import ui

from smart_decision_miniproject.hmi.task1_page import (
    render_algorithm_comparison_content,
)
from smart_decision_miniproject.hmi.task2_page import (
    render_parameter_optimization_content,
)
from smart_decision_miniproject.hmi.task3_page import render_report_content

# 全局状态变量
current_page = "home"
main_content = None


def render_home_content():
    """渲染主页内容"""
    with ui.column().classes("w-full"):
        ui.label("Mini Projet de Décision Intelligente").classes(
            "text-h3 text-center q-mt-lg q-mb-md text-grey-8"
        )
        ui.separator().classes("q-mb-lg")

        # 内容卡片
        with ui.card().classes("w-full q-ma-md"):
            with ui.card_section():
                ui.label("Aperçu du Projet").classes("text-h5 text-primary q-mb-md")
                ui.label(
                    "Ce site web est spécialement conçu pour le Mini Projet du cours Smart Decision 2025 de Centrale Pékin, réalisé par Philippe et Grégory.\nIl comprend les travaux suivants :"
                ).classes("text-body1 q-mb-sm")

                with ui.list().classes("q-pl-md"):
                    ui.item_label("• Comparer, à différentes échelles, les performances temporelles de l’algorithme du recuit simulé et de l’algorithme des colonies de fourmis appliqués au problème du TSP.")
                    ui.item_label(
                        "• Résoudre le problème du TSP sur une carte géographique réelle avec des emplacements sélectionnables, en utilisant le recuit simulé et l’algorithme des colonies de fourmis."
                    )
                    ui.item_label(
                        "• Résoudre le problème du TSP sur une carte géographique réelle avec des emplacements sélectionnables, en utilisant le recuit simulé et l’algorithme des colonies de fourmis."
                    )

        # 功能模块卡片
        with ui.row().classes("w-full q-gutter-md q-ma-md"):
            with ui.card().classes("flex-1"):
                with ui.card_section():
                    ui.icon("timeline", size="2em").classes("text-primary")
                    ui.label("Analyse d'Algorithmes").classes("text-h6 q-mt-sm")
                    ui.label(
                        "Comparer les performances de différents algorithmes"
                    ).classes("text-caption text-grey-6")

            with ui.card().classes("flex-1"):
                with ui.card_section():
                    ui.icon("settings", size="2em").classes("text-primary")
                    ui.label("Configuration de Paramètres").classes("text-h6 q-mt-sm")
                    ui.label("Ajuster les paramètres et réglages d'exécution").classes(
                        "text-caption text-grey-6"
                    )

            with ui.card().classes("flex-1"):
                with ui.card_section():
                    ui.icon("bar_chart", size="2em").classes("text-primary")
                    ui.label("Affichage des Résultats").classes("text-h6 q-mt-sm")
                    ui.label("Visualisation des résultats d'analyse").classes(
                        "text-caption text-grey-6"
                    )


def update_main_content(page_name):
    """更新主内容区域"""
    global current_page, main_content
    current_page = page_name
    print(f"切换到页面: {page_name}")  # 调试信息
    
    # 根据页面动态更新浏览器标题
    page_titles = {
        "home": "Accueil | Mini Projet - Décision Intelligente",
        "algorithm_comparison": "Comparaison d'Algorithmes | Mini Projet TSP",
        "parameter_optimization": "Optimisation Géographique | Mini Projet TSP", 
        "report": "Résolution VRP | Mini Projet - Vehicle Routing"
    }
    
    title = page_titles.get(page_name, "Mini Projet - Décision Intelligente")
    ui.page_title(title)

    # 清空当前内容并重新渲染
    if main_content is not None:
        main_content.clear()

        # 根据页面名称渲染对应内容
        with main_content:
            if page_name == "home":
                render_home_content()
            elif page_name == "algorithm_comparison":
                render_algorithm_comparison_content()
            elif page_name == "parameter_optimization":
                render_parameter_optimization_content()
            elif page_name == "report":
                render_report_content()
            else:
                ui.label(f'页面 "{page_name}" 未找到').classes(
                    "text-h4 text-center q-mt-lg"
                )
    else:
        print("main_content 是 None")


def main_page_layout():
    global main_content
    
    # 设置页面基本信息
    ui.page_title('Mini Projet - Décision Intelligente | TSP & VRP Solver')
    ui.add_head_html('<meta name="description" content="Application de résolution TSP et VRP avec algorithmes de recuit simulé et colonies de fourmis">')
    ui.add_head_html('<meta name="keywords" content="TSP, VRP, Recuit Simulé, Colonies de Fourmis, Optimisation">')

    # 顶部导航栏
    with (
        ui.header(elevated=True)
        .style("background-color: #3874c8")
        .classes("items-center justify-between q-px-lg")
    ):
        ui.label("Mini Projet de Décision Intelligente").classes(
            "text-h5 text-white text-weight-medium"
        )
        ui.button(on_click=lambda: right_drawer.toggle(), icon="menu").props(
            "flat color=white"
        ).classes("q-ml-auto")

    # 左侧任务栏
    with ui.left_drawer(top_corner=False, bottom_corner=False).style(
        "background-color: #f5f7fa"
    ):
        ui.label("Liste des Tâches").classes(
            "text-h6 q-pa-lg text-primary text-weight-medium"
        )
        ui.separator()

        with ui.column().classes("q-pa-md q-gutter-sm"):
            # 算法比较按钮 - 强调对比
            with ui.row().classes("full-width"):
                with ui.button(
                    icon="compare_arrows",
                    on_click=lambda: update_main_content("algorithm_comparison"),
                ).props("flat color=green-6").classes("q-mr-sm"):
                    pass
                with ui.column().classes("flex-1 cursor-pointer").on('click', lambda: update_main_content("algorithm_comparison")):
                    ui.label("Exécuter Comparaison d'Algorithmes").classes("text-subtitle1 text-weight-medium")
                    ui.label("Effectuer test de performance TSP").classes("text-caption text-grey-6")

            ui.separator().classes("q-my-sm")

            # 参数优化按钮 - 强调真实地理图
            with ui.row().classes("full-width"):
                with ui.button(
                    icon="map",
                    on_click=lambda: update_main_content("parameter_optimization"),
                ).props("flat color=blue-6").classes("q-mr-sm"):
                    pass
                with ui.column().classes("flex-1 cursor-pointer").on('click', lambda: update_main_content("parameter_optimization")):
                    ui.label("Optimisation de Paramètres").classes("text-subtitle1 text-weight-medium")
                    ui.label("Ajuster les hyperparamètres d'algorithme").classes("text-caption text-grey-6")

            ui.separator().classes("q-my-sm")

            # 报告按钮 - 强调VLP
            with ui.row().classes("full-width"):
                with ui.button(
                    icon="psychology",
                    on_click=lambda: update_main_content("report"),
                ).props("flat color=orange-6").classes("q-mr-sm"):
                    pass
                with ui.column().classes("flex-1 cursor-pointer").on('click', lambda: update_main_content("report")):
                    ui.label("Consulter le Rapport").classes("text-subtitle1 text-weight-medium")
                    ui.label("Analyser les résultats de test").classes("text-caption text-grey-6")

            ui.separator().classes("q-my-md")

            # 返回主页按钮
            with ui.button(
                "Retour à l'Accueil",
                icon="home",
                on_click=lambda: update_main_content("home")
            ).props("outline color=primary full-width").classes("q-py-md"):
                pass

    # 主内容区域容器
    main_content = ui.column().classes("w-full")

    # 初始化显示主页
    update_main_content("home")

    # 右侧设置面板
    with (
        ui.right_drawer(fixed=False, value=False)
        .style("background-color: #f5f7fa")
        .props("bordered") as right_drawer
    ):
        ui.label("Paramètres Système").classes(
            "text-h6 q-pa-lg text-primary text-weight-medium"
        )
        ui.separator()

        with ui.column().classes("q-pa-lg q-gutter-md"):
            ui.label("Thème d'Interface").classes("text-subtitle2 text-weight-medium")
            ui.select(["Thème Clair", "Thème Sombre"], value="Thème Clair").classes(
                "q-mb-md"
            )

            ui.label("Paramètres de Langue").classes(
                "text-subtitle2 text-weight-medium"
            )
            ui.select(["Français", "English", "中文"], value="Français").classes(
                "q-mb-md"
            )

            ui.separator()

            ui.label("Paramètres d'Algorithme").classes(
                "text-subtitle2 text-weight-medium"
            )
            ui.checkbox("Activer journal détaillé").classes("q-mb-sm")
            ui.checkbox("Sauvegarde automatique des résultats").classes("q-mb-sm")

    # 底部信息栏
    with (
        ui.footer()
        .style("background-color: #3874c8; padding: 8px 24px;")
        .classes("justify-between items-center")
    ):
        ui.label("© 2025 Projet de Décision Intelligente").classes(
            "text-body2 text-white"
        )
        ui.label("Réalisé par Philippe et Gregory").classes(
            "text-body2 text-white text-weight-medium"
        )


main_page_layout()

ui.run()
