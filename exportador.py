import os

def exportar_codigo_fuente():
    """
    Recorre el directorio actual y extrae el contenido de los archivos de código fuente
    para consolidarlos en un único archivo de texto. Omite carpetas de dependencias y binarios.
    """
    directorio_raiz = "."
    archivo_salida = "codigo_completo_ptar.txt"
    
    # Directorios que no deben ser analizados para evitar sobrecarga de texto
    directorios_excluidos = {
        '.git', 
        'node_modules', 
        '__pycache__', 
        'venv', 
        '.venv', 
        'env', 
        'dist', 
        'build', 
        '.vscode', 
        '.idea', 
        'pg_data', 
        'ollama_data',
        'postgres_data'
    }
    
    # Extensiones de archivos binarios o irrelevantes que deben ignorarse
    extensiones_excluidas = {
        '.pyc', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', 
        '.pdf', '.onnx', '.db', '.sqlite3', '.exe', '.dll', '.so', 
        '.zip', '.tar', '.gz', '.mp4', '.woff', '.woff2', '.ttf', '.eot',
        '.pkl', '.h5', '.pt', '.bin'
    }

    archivos_procesados = 0

    with open(archivo_salida, 'w', encoding='utf-8') as salida:
        for directorio_actual, subdirectorios, archivos in os.walk(directorio_raiz):
            # Modificar la lista de subdirectorios en su lugar para omitir los excluidos
            subdirectorios[:] = [d for d in subdirectorios if d not in directorios_excluidos]
            
            for nombre_archivo in archivos:
                extension = os.path.splitext(nombre_archivo)[1].lower()
                
                # Ignorar el propio script de exportación y el archivo de salida
                if extension in extensiones_excluidas or nombre_archivo in ["exportador.py", archivo_salida]:
                    continue
                
                ruta_completa = os.path.join(directorio_actual, nombre_archivo)
                ruta_relativa = os.path.relpath(ruta_completa, directorio_raiz)
                
                try:
                    # Se utiliza errors='replace' para no detener el script si encuentra un byte no decodificable
                    with open(ruta_completa, 'r', encoding='utf-8', errors='replace') as entrada:
                        contenido = entrada.read()
                    
                    salida.write(f"{'='*80}\n")
                    salida.write(f"ARCHIVO: {ruta_relativa}\n")
                    salida.write(f"{'='*80}\n\n")
                    salida.write(contenido)
                    salida.write("\n\n")
                    archivos_procesados += 1
                    
                except Exception as e:
                    salida.write(f"{'='*80}\n")
                    salida.write(f"ERROR LEYENDO ARCHIVO: {ruta_relativa} - {str(e)}\n")
                    salida.write(f"{'='*80}\n\n")

    print(f"Exportación finalizada. {archivos_procesados} archivos consolidados en '{archivo_salida}'.")

if __name__ == "__main__":
    exportar_codigo_fuente()