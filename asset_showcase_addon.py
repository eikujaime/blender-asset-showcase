# [EL CÓDIGO COMPLETO DEL ADDON IRÁ AQUÍ]
# Crear una estructura adecuada para Blender: carpeta + archivo .py dentro del zip
addon_folder_name = "asset_showcase_addon"
addon_base_path = f"/mnt/data/{addon_folder_name}"
addon_file_path = os.path.join(addon_base_path, "__init__.py")  # nombre correcto para un addon

# Código completo del addon
addon_code = """
bl_info = {
    "name": "Asset Showcase",
    "author": "Eiku",
    "version": (1, 0),
    "blender": (3, 5, 0),
    "location": "View3D > Sidebar > Assets",
    "description": "Crea una escena para mostrar modelos 3D, los importa y renderiza automáticamente.",
    "category": "3D View",
}

import bpy
import math
import os
import datetime
from bpy.props import StringProperty
from bpy.types import Operator, Panel

class CrearEscenarioComplejo(bpy.types.Operator):
    bl_idname = "object.crear_escenario_complejo"
    bl_label = "Crear Escenario para Assets"
    bl_description = "Genera un entorno elegante para exhibir modelos 3D"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

        bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=0.3, location=(0, 0, 0.15))
        plataforma = bpy.context.active_object
        plataforma.name = "Plataforma"

        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=4, depth=4, location=(0, 0, 2))
        fondo = bpy.context.active_object
        fondo.name = "Fondo"
        fondo.scale[0] = 1
        fondo.scale[1] = 0.5
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='ONLY_FACE')
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
        suelo = bpy.context.active_object
        suelo.name = "Suelo"

        def crear_luz(nombre, tipo, energia, loc, rot):
            bpy.ops.object.light_add(type=tipo, location=loc, rotation=rot)
            luz = bpy.context.active_object
            luz.data.energy = energia
            luz.name = nombre
            return luz

        crear_luz("Luz_Techo", "AREA", 1200, (0, 0, 5), (math.radians(-90), 0, 0))
        crear_luz("Luz_Lado_Izq", "AREA", 500, (-3, 0, 3), (math.radians(-60), 0, math.radians(30)))
        crear_luz("Luz_Lado_Der", "AREA", 500, (3, 0, 3), (math.radians(-60), 0, math.radians(-30)))

        bpy.ops.object.camera_add(location=(4, -4, 3), rotation=(math.radians(60), 0, math.radians(45)))
        cam1 = bpy.context.active_object
        cam1.name = "Camara_Angulo"
        bpy.context.scene.camera = cam1

        def crear_material(nombre, color, brillo=0.5):
            mat = bpy.data.materials.new(name=nombre)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            bsdf.inputs["Base Color"].default_value = (*color, 1)
            bsdf.inputs["Roughness"].default_value = brillo
            return mat

        suelo.data.materials.append(crear_material("Suelo_Negro", (0.1, 0.1, 0.1), 0.3))
        fondo.data.materials.append(crear_material("Fondo_Gris", (0.3, 0.3, 0.3), 0.6))
        plataforma.data.materials.append(crear_material("Plataforma_Luz", (0.8, 0.8, 0.8), 0.4))

        self.report({'INFO'}, "✅ Escenario generado correctamente.")
        return {'FINISHED'}


class ImportarModeloAsset(bpy.types.Operator):
    bl_idname = "object.importar_asset_modelo"
    bl_label = "Importar y Posicionar Modelo"
    bl_description = "Importa un modelo 3D y lo posiciona sobre la plataforma"
    filepath: StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        ext = os.path.splitext(self.filepath)[-1].lower()

        if ext == ".obj":
            bpy.ops.import_scene.obj(filepath=self.filepath)
        elif ext == ".fbx":
            bpy.ops.import_scene.fbx(filepath=self.filepath)
        elif ext == ".blend":
            with bpy.data.libraries.load(self.filepath) as (data_from, data_to):
                data_to.objects = data_from.objects
            for obj in data_to.objects:
                if obj is not None:
                    bpy.context.collection.objects.link(obj)
        else:
            self.report({'ERROR'}, "Formato no soportado.")
            return {'CANCELLED'}

        objeto = bpy.context.selected_objects[0]
        objeto.name = "Asset_Importado"
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        objeto.location = (0, 0, 0.3)

        max_dim = max(objeto.dimensions)
        if max_dim > 3:
            factor = 3 / max_dim
            objeto.scale = (factor, factor, factor)

        self.report({'INFO'}, f"✅ Modelo importado: {objeto.name}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class RenderizarYExportar(bpy.types.Operator):
    bl_idname = "render.exportar_imagen_asset"
    bl_label = "Renderizar y Guardar Imagen"
    bl_description = "Renderiza la vista de cámara y guarda la imagen como PNG"
    bl_options = {'REGISTER'}

    def execute(self, context):
        blend_path = bpy.data.filepath
        if not blend_path:
            self.report({'ERROR'}, "¡Guardá primero el archivo .blend!")
            return {'CANCELLED'}

        carpeta = os.path.join(os.path.dirname(blend_path), "renders")
        os.makedirs(carpeta, exist_ok=True)

        fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre = os.path.splitext(os.path.basename(blend_path))[0]
        archivo = f"{nombre}_{fecha}.png"
        ruta_completa = os.path.join(carpeta, archivo)

        scene = bpy.context.scene
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = ruta_completa
        bpy.ops.render.render(write_still=True)

        self.report({'INFO'}, f"✅ Imagen guardada: {ruta_completa}")
        return {'FINISHED'}


class PANEL_EscenaAssets(bpy.types.Panel):
    bl_label = "Asset Showcase"
    bl_idname = "VIEW3D_PT_asset_showcase"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Assets'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.crear_escenario_complejo", icon='SCENE_DATA')
        layout.separator()
        layout.operator("object.importar_asset_modelo", icon='IMPORT')
        layout.separator()
        layout.operator("render.exportar_imagen_asset", icon='RENDER_RESULT')


classes = [
    CrearEscenarioComplejo,
    ImportarModeloAsset,
    RenderizarYExportar,
    PANEL_EscenaAssets,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
"""

# Crear carpeta y archivo
os.makedirs(addon_base_path, exist_ok=True)
with open(addon_file_path, "w", encoding="utf-8") as f:
    f.write(addon_code.strip())

# Crear .zip correctamente estructurado
final_zip_path = "/mnt/data/asset_showcase_addon_pro.zip"
with ZipFile(final_zip_path, "w") as zipf:
    for root, dirs, files in os.walk(addon_base_path):
        for file in files:
            filepath = os.path.join(root, file)
            arcname = os.path.relpath(filepath, "/mnt/data")
            zipf.write(filepath, arcname)

final_zip_path
