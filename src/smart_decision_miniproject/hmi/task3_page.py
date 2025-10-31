import asyncio
import io
from nicegui import ui
import plotly.graph_objects as go
from smart_decision_miniproject.solver.VRP import solve_solomon_vrp, VRPResult

# 全局变量
uploaded_file_content: str = ""
vrp_result = None
is_solving = False
results_container = None

def render_report_content():
    """渲染Solomon VRP求解页面内容"""
    global uploaded_file_content, vrp_result
    
    # 主容器，居中并限制最大宽度
    with ui.column().classes('w-full max-w-6xl mx-auto q-px-md'):
        # 页面标题
        ui.label('Résolveur VRP Solomon').classes('text-h3 text-center q-mt-lg q-mb-xl text-primary')
        
        # 第一个区域：文件上传区域
        with ui.card().classes('w-full q-mb-xl shadow-lg q-pa-lg'):
            ui.label('📁 Téléchargement de Fichier Solomon').classes('text-h5 text-primary q-mb-lg text-center')
            
            # 文件上传说明
            with ui.card().classes('w-full bg-blue-1 q-pa-lg q-mb-lg'):
                ui.label('ℹ️ Instructions de Téléchargement').classes('text-h6 text-blue-8 q-mb-md')
                ui.html('''
                <ul class="text-subtitle2 text-blue-7">
                    <li>Téléchargez un fichier de données Solomon (format .txt)</li>
                    <li>Le fichier doit contenir les informations sur les clients, véhicules et contraintes</li>
                    <li>Formats supportés: C101, R101, RC101, etc.</li>
                    <li>Exemple de structure requise: coordonnées, demandes, fenêtres temporelles</li>
                </ul>
                ''', sanitize=False)
            
            # 文件上传控件 - 使用异步回调
            with ui.row().classes('w-full justify-center q-gutter-lg'):
                with ui.column().classes('items-center'):
                    async def handle_upload(e):
                        await handle_file_upload_async(e)
                    
                    upload_area = ui.upload(
                        on_upload=handle_upload,
                        multiple=False,
                        max_file_size=10_000_000,  # 10MB
                        auto_upload=True
                    ).props('accept=".txt,.dat" color=primary').classes('q-pa-lg')
                    upload_area.classes('border-2 border-dashed border-primary rounded-lg')
                    
                    ui.label('Glissez-déposez votre fichier ici ou cliquez pour sélectionner').classes(
                        'text-center text-grey-6 q-mt-md'
                    )
            
            # 添加手动输入功能作为备选
            with ui.row().classes('w-full justify-center q-gutter-lg q-mt-lg'):
                ui.button(
                    'Utiliser Données de Test',
                    icon='science',
                    on_click=load_test_data
                ).props('color=blue size=md outline').classes('q-px-lg')
            
            # 文件信息显示区域
            file_info_container = ui.column().classes('w-full q-mt-lg')
        
        # 第二个区域：求解控制
        with ui.card().classes('w-full q-mb-xl shadow-lg q-pa-lg'):
            ui.label('🔧 Contrôle de Résolution').classes('text-h5 text-primary q-mb-lg text-center')
            
            # 控制按钮
            with ui.row().classes('w-full justify-center q-gutter-lg q-mb-lg'):
                solve_button = ui.button(
                    'Résoudre VRP',
                    icon='play_arrow',
                    on_click=lambda: asyncio.create_task(solve_vrp())
                ).props('color=positive size=lg unelevated').classes('q-px-xl')
                
                reset_button = ui.button(
                    'Réinitialiser',
                    icon='refresh',
                    on_click=reset_results
                ).props('color=grey size=lg outline').classes('q-px-xl')
            
            # 进度显示
            progress_container = ui.column().classes('w-full')
            with progress_container:
                with ui.card().classes('w-full bg-grey-2 q-pa-lg'):
                    ui.label('Statut').classes('text-h6 text-center q-mb-md text-weight-medium')
                    status_label = ui.label('En attente de fichier...').classes(
                        'text-center text-grey-6'
                    )
        
        # 第三个区域：结果展示
        global results_container
        results_container = ui.column().classes('w-full')
        with results_container:
            with ui.card().classes('w-full shadow-lg q-pa-lg'):
                ui.label('📊 Résultats de Résolution').classes('text-h5 text-primary q-mb-lg text-center')
                
                # 结果内容容器
                results_content = ui.column().classes('w-full')
                with results_content:
                    with ui.column().classes('items-center justify-center q-pa-xl'):
                        ui.icon('assessment', size='4em').classes('text-grey-5')
                        ui.label('Les résultats apparaîtront ici après la résolution').classes(
                            'text-center text-grey-6'
                        )


def load_test_data():
    """加载测试数据"""
    global uploaded_file_content
    
    test_data = """C101

VEHICLE
NUMBER     CAPACITY
  25         200

CUSTOMER
CUST NO.  XCOORD.   YCOORD.    DEMAND   READY TIME  DUE DATE   SERVICE   TIME
 
    0      40         50          0          0       1236          0   
    1      45         68         10        912        967         90   
    2      45         70         30        825        870         90   
    3      42         66         10         65        146         90   
    4      42         68         10        727        782         90   
    5      42         65         10         15         67         90   
    6      40         69         20        621        702         90   
    7      40         66         20        170        225         90"""
    
    uploaded_file_content = test_data
    print('Données de test C101 chargées avec succès!')
    
    # 显示文件预览
    show_file_preview("C101_test.txt", uploaded_file_content)
    
    # 更新状态
    update_status('Données de test chargées. Prêt pour la résolution.')


def handle_file_upload_sync(e):
    """同步处理文件上传"""
    global uploaded_file_content
    
    print(f"上传事件触发，文件信息: {getattr(e, 'name', 'unknown')}")
    print(f"事件属性: {[attr for attr in dir(e) if not attr.startswith('_')]}")
    
    try:
        # 尝试多种方式获取文件内容
        content = None
        
        # 方法1: 通过file属性读取
        if hasattr(e, 'file') and e.file:
            try:
                # 读取文件内容
                content = e.file.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                print("成功通过file属性读取文件")
            except Exception as ex:
                print(f"通过file属性读取失败: {ex}")
                # 尝试重置文件指针并重新读取
                try:
                    e.file.seek(0)
                    content = e.file.read()
                    if isinstance(content, bytes):
                        content = content.decode('utf-8')
                    print("重置文件指针后成功读取")
                except Exception as ex2:
                    print(f"重置后仍然失败: {ex2}")
        
        # 方法2: 直接访问content属性
        elif hasattr(e, 'content') and e.content is not None:
            if isinstance(e.content, bytes):
                content = e.content.decode('utf-8')
            else:
                content = str(e.content)
            print("成功通过content属性读取文件")
            
        # 方法3: 访问text属性
        elif hasattr(e, 'text') and e.text:
            content = e.text
            print("成功通过text属性读取文件")
            
        # 方法4: 访问data属性
        elif hasattr(e, 'data') and e.data:
            if isinstance(e.data, bytes):
                content = e.data.decode('utf-8')
            else:
                content = str(e.data)
            print("成功通过data属性读取文件")
        
        if content and content.strip():
            # 确保内容是字符串类型
            if isinstance(content, bytes):
                uploaded_file_content = content.decode('utf-8')
            else:
                uploaded_file_content = str(content)
                
            filename = getattr(e, 'name', 'uploaded_file')
            print(f'Fichier "{filename}" téléchargé avec succès!')
            print(f'Taille du contenu: {len(uploaded_file_content)} caractères')
            print(f'Aperçu du contenu: {uploaded_file_content[:100]}...')
            
            # 显示文件预览
            show_file_preview(filename, uploaded_file_content)
            
            # 更新状态
            update_status('Fichier téléchargé. Prêt pour la résolution.')
        else:
            raise Exception("Le fichier semble être vide ou illisible")
        
    except Exception as ex:
        print(f'Erreur lors du téléchargement: {str(ex)}')
        uploaded_file_content = ""
        update_status('Erreur lors du téléchargement du fichier')


async def handle_file_upload_async(e):
    """异步处理文件上传"""
    global uploaded_file_content
    
    print(f"异步上传事件触发，文件信息: {getattr(e, 'name', 'unknown')}")
    print(f"事件属性: {[attr for attr in dir(e) if not attr.startswith('_')]}")
    
    try:
        content = None
        
        # 方法1: 通过file属性异步读取
        if hasattr(e, 'file') and e.file:
            try:
                # 异步读取文件内容
                content = await e.file.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                print("成功通过异步file属性读取文件")
            except Exception as ex:
                print(f"异步读取失败: {ex}")
        
        # 方法2: 尝试其他属性
        elif hasattr(e, 'content') and e.content is not None:
            if isinstance(e.content, bytes):
                content = e.content.decode('utf-8')
            else:
                content = str(e.content)
            print("成功通过content属性读取文件")
        
        if content and content.strip():
            # 确保内容是字符串类型
            uploaded_file_content = str(content)
                
            filename = getattr(e, 'name', 'uploaded_file')
            print(f'Fichier "{filename}" téléchargé avec succès!')
            print(f'Taille du contenu: {len(uploaded_file_content)} caractères')
            print(f'Aperçu du contenu: {uploaded_file_content[:100]}...')
            
            # 显示文件预览
            show_file_preview(filename, uploaded_file_content)
            
            # 更新状态
            update_status('Fichier téléchargé. Prêt pour la résolution.')
        else:
            raise Exception("Le fichier semble être vide ou illisible")
        
    except Exception as ex:
        print(f'Erreur lors du téléchargement: {str(ex)}')
        uploaded_file_content = ""
        update_status('Erreur lors du téléchargement du fichier')


def handle_file_upload(e):
    """处理文件上传"""
    global uploaded_file_content
    
    try:
        # 读取文件内容 - 使用正确的属性访问方式
        if hasattr(e, 'content'):
            uploaded_file_content = e.content.decode('utf-8')
        elif hasattr(e, 'bytes'):
            uploaded_file_content = e.bytes.decode('utf-8')
        else:
            # 尝试通过文件路径读取
            with open(e.name, 'r', encoding='utf-8') as f:
                uploaded_file_content = f.read()
        
        # 更新UI显示文件信息
        print(f'Fichier "{e.name}" téléchargé avec succès!')
        
        # 显示文件预览
        show_file_preview(e.name, uploaded_file_content)
        
        # 更新状态
        update_status('Fichier téléchargé. Prêt pour la résolution.')
        
    except Exception as ex:
        print(f'Erreur lors du téléchargement: {str(ex)}')
        print(f'Attributs disponibles dans l\'événement: {dir(e)}')
        uploaded_file_content = ""


def show_file_preview(filename: str, content: str):
    """显示文件预览"""
    # 这里可以添加文件内容的预览显示
    lines = content.split('\n')
    preview_lines = lines[:10]  # 显示前10行
    
    # 找到文件信息显示容器并更新
    # 注意：在实际实现中，你需要通过全局变量或其他方式访问容器
    print(f"文件 {filename} 已上传，包含 {len(lines)} 行数据")
    print("文件预览（前10行）:")
    for i, line in enumerate(preview_lines):
        print(f"{i+1}: {line}")


def update_status(message: str):
    """更新状态标签"""
    # 在实际实现中，需要通过全局变量访问status_label
    print(f"状态更新: {message}")


async def solve_vrp():
    """求解VRP问题"""
    global uploaded_file_content, vrp_result, is_solving
    
    if not uploaded_file_content or not uploaded_file_content.strip():
        print('Veuillez d\'abord télécharger un fichier Solomon')
        return
    
    if is_solving:
        print('Résolution déjà en cours...')
        return
    
    is_solving = True
    update_status('Résolution en cours...')
    
    try:
        # 在后台线程中求解VRP
        vrp_result = solve_solomon_vrp(uploaded_file_content)
        
        # 显示结果
        show_vrp_results(vrp_result)
        
        print('Résolution terminée avec succès!')
        update_status(f'Résolution terminée en {vrp_result.solve_time:.2f} secondes')
        
    except Exception as ex:
        print(f'Erreur lors de la résolution: {str(ex)}')
        update_status('Erreur lors de la résolution')
        print(f"错误详情: {ex}")
    
    finally:
        is_solving = False


def show_vrp_results(result: VRPResult):
    """在前端界面显示VRP求解结果"""
    global results_container
    
    if results_container is None:
        print("错误：results_container未初始化")
        return
    
    # 清空之前的结果
    results_container.clear()
    
    with results_container:
        with ui.card().classes('w-full shadow-lg q-pa-lg'):
            ui.label('📊 Résultats de Résolution').classes('text-h5 text-primary q-mb-lg text-center')
            
            # 基本统计信息
            with ui.row().classes('w-full q-gutter-md q-mb-lg'):
                with ui.card().classes('col bg-positive text-white'):
                    with ui.column().classes('items-center q-pa-md'):
                        ui.label(f'{result.total_distance:.2f}').classes('text-h4 text-weight-bold')
                        ui.label('Distance Totale').classes('text-subtitle1')
                
                with ui.card().classes('col bg-info text-white'):
                    with ui.column().classes('items-center q-pa-md'):
                        ui.label(f'{result.num_vehicles_used}').classes('text-h4 text-weight-bold')
                        ui.label('Véhicules Utilisés').classes('text-subtitle1')
                
                with ui.card().classes('col bg-accent text-white'):
                    with ui.column().classes('items-center q-pa-md'):
                        ui.label(f'{result.solve_time:.3f}s').classes('text-h4 text-weight-bold')
                        ui.label('Temps de Résolution').classes('text-subtitle1')
            
            # 获取详细统计信息
            statistics = result.get_statistics()
            
            # # 详细统计表格
            # with ui.expansion('Statistiques Détaillées', icon='analytics').classes('w-full q-mb-md'):
            #     with ui.grid(columns=2).classes('w-full gap-4'):
            #         for key, value in statistics.items():
            #             if key != 'routes_details':
            #                 ui.label(f'{key}:').classes('text-weight-medium')
            #                 ui.label(str(value)).classes('text-right')
            
            # 详细路线信息
            with ui.expansion('Détails des Routes', icon='route').classes('w-full q-mb-md'):
                for route_detail in statistics.get('routes_details', []):
                    with ui.card().classes('q-mb-sm'):
                        ui.label(f'Route {route_detail["route_id"]}: {route_detail["customers"]}').classes('text-body1 q-mb-xs')
                        ui.label(f'Distance: {route_detail["route_distance"]:.2f}').classes('text-caption text-grey-6')
                        ui.label(f'Demande totale: {route_detail["total_demand"]}').classes('text-caption text-grey-6')
            
            # 直接在这里创建图表，而不是调用separate function
            with ui.card().classes('w-full q-mt-md'):
                ui.label('Visualisation des Routes').classes('text-h6 text-primary q-mb-md text-center')
                
                # 创建路径图表
                fig = go.Figure()
                
                # 添加客户点
                x_coords = [customer.x for customer in result.customers]
                y_coords = [customer.y for customer in result.customers]
                
                # 仓库点
                fig.add_trace(go.Scatter(
                    x=[x_coords[0]],
                    y=[y_coords[0]],
                    mode='markers',
                    marker=dict(size=15, color='red', symbol='square'),
                    name='Dépôt',
                    hovertemplate='Dépôt<br>X: %{x}<br>Y: %{y}<extra></extra>'
                ))
                
                # 客户点
                fig.add_trace(go.Scatter(
                    x=x_coords[1:],
                    y=y_coords[1:],
                    mode='markers',
                    marker=dict(size=8, color='blue', symbol='circle'),
                    name='Clients',
                    hovertemplate='Client %{pointNumber}<br>X: %{x}<br>Y: %{y}<extra></extra>'
                ))
                
                # 添加路径线
                colors = ['green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
                for i, route in enumerate(result.routes):
                    if not route:
                        continue
                        
                    # 构建路径坐标（包括从仓库出发和返回仓库）
                    route_x = [x_coords[0]]  # 从仓库开始
                    route_y = [y_coords[0]]
                    
                    for customer_id in route:
                        route_x.append(x_coords[customer_id])
                        route_y.append(y_coords[customer_id])
                    
                    route_x.append(x_coords[0])  # 返回仓库
                    route_y.append(y_coords[0])
                    
                    color = colors[i % len(colors)]
                    fig.add_trace(go.Scatter(
                        x=route_x,
                        y=route_y,
                        mode='lines',
                        line=dict(color=color, width=2),
                        name=f'Route {i+1}',
                        hovertemplate=f'Route {i+1}<extra></extra>'
                    ))
                
                fig.update_layout(
                    title=dict(
                        text='Solutions VRP - Routes des Véhicules',
                        font=dict(size=16, color="#2c3e50"),
                        x=0.5,
                        xanchor='center'
                    ),
                    xaxis=dict(title='Coordonnée X'),
                    yaxis=dict(title='Coordonnée Y'),
                    template="plotly_white",
                    height=500,
                    showlegend=True
                )
                
                ui.plotly(fig).classes('w-full')
    
    # 也在控制台输出结果供调试
    print("=== Résultats VRP ===")
    print(f"Nombre de véhicules utilisés: {result.num_vehicles_used}")
    print(f"Distance totale: {result.total_distance:.2f}")
    print(f"Temps de résolution: {result.solve_time:.3f} secondes")
    
    print("\nStatistiques détaillées:")
    for key, value in statistics.items():
        if key != 'routes_details':
            print(f"  {key}: {value}")
    
    print("\nDétails des routes:")
    for route_detail in statistics.get('routes_details', []):
        print(f"  Route {route_detail['route_id']}: {route_detail['customers']}")
        print(f"    Distance: {route_detail['route_distance']:.2f}")
        print(f"    Demande totale: {route_detail['total_demand']}")
    print("=" * 30)


def create_results_visualization(result: VRPResult):
    """创建结果可视化"""
    global results_container
    
    if results_container is None:
        print("错误：results_container未初始化，无法显示图表")
        return
    
    # 创建路径图表
    fig = go.Figure()
    
    # 添加客户点
    x_coords = [customer.x for customer in result.customers]
    y_coords = [customer.y for customer in result.customers]
    
    # 仓库点
    fig.add_trace(go.Scatter(
        x=[x_coords[0]],
        y=[y_coords[0]],
        mode='markers',
        marker=dict(size=15, color='red', symbol='square'),
        name='Dépôt',
        hovertemplate='Dépôt<br>X: %{x}<br>Y: %{y}<extra></extra>'
    ))
    
    # 客户点
    fig.add_trace(go.Scatter(
        x=x_coords[1:],
        y=y_coords[1:],
        mode='markers',
        marker=dict(size=8, color='blue', symbol='circle'),
        name='Clients',
        hovertemplate='Client %{pointNumber}<br>X: %{x}<br>Y: %{y}<extra></extra>'
    ))
    
    # 添加路径线
    colors = ['green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
    for i, route in enumerate(result.routes):
        if not route:
            continue
            
        # 构建路径坐标（包括从仓库出发和返回仓库）
        route_x = [x_coords[0]]  # 从仓库开始
        route_y = [y_coords[0]]
        
        for customer_id in route:
            route_x.append(x_coords[customer_id])
            route_y.append(y_coords[customer_id])
        
        route_x.append(x_coords[0])  # 返回仓库
        route_y.append(y_coords[0])
        
        color = colors[i % len(colors)]
        fig.add_trace(go.Scatter(
            x=route_x,
            y=route_y,
            mode='lines',
            line=dict(color=color, width=2),
            name=f'Route {i+1}',
            hovertemplate=f'Route {i+1}<extra></extra>'
        ))
    
    fig.update_layout(
        title=dict(
            text='Solutions VRP - Routes des Véhicules',
            font=dict(size=16, color="#2c3e50"),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(title='Coordonnée X'),
        yaxis=dict(title='Coordonnée Y'),
        template="plotly_white",
        height=500,
        showlegend=True
    )
    
    # 将图表添加到结果容器中
    with results_container:
        with ui.card().classes('w-full q-mt-md'):
            ui.label('Visualisation des Routes').classes('text-h6 text-primary q-mb-md text-center')
            ui.plotly(fig).classes('w-full')
    
    print("图表已创建并显示在UI中")


def reset_results():
    """重置结果"""
    global uploaded_file_content, vrp_result, is_solving
    
    uploaded_file_content = ""
    vrp_result = None
    is_solving = False
    
    update_status('Réinitialisé. En attente de fichier...')
    print('Résultats réinitialisés')
    
    print("结果已重置")