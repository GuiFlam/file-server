from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import json
from urllib.parse import parse_qs
import socket

UPLOAD_DIR = "uploads"
HTML_FILE = "index.html"
DOWNLOAD_DIR = "downloads"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class FileUploadHandler(BaseHTTPRequestHandler):
     def do_POST(self):
        if self.path == '/upload':
            self.handle_file_upload()
        else:
            self.send_error(404, "Not Found")

     def handle_file_upload(self):
        try:
            content_length = int(self.headers['Content-Length'])
            content_type = self.headers.get('Content-Type', '')

            if not content_length or 'multipart/form-data' not in content_type:
                self.send_error(400, "Invalid request: Content-Type must be multipart/form-data.")
                return

            boundary = content_type.split("boundary=")[1].encode()
            body = self.rfile.read(content_length)

            parts = body.split(boundary)

            filename = None
            for part in parts[1:-1]:
                if b"\r\n\r\n" not in part:
                    continue

                headers, file_data = part.split(b"\r\n\r\n", 1)
                headers = headers.decode()

                for header in headers.split("\r\n"):
                    if "Content-Disposition" in header and "filename=" in header:
                        filename = header.split('filename="')[1].split('"')[0]
                        break

                if not filename:
                    self.send_error(400, "No filename provided in the request.")
                    return

                filepath = os.path.join(UPLOAD_DIR, filename)
                with open(filepath, 'wb') as f:
                    f.write(file_data.strip(b"--").strip())

                print(f"File uploaded: {filename}")

            response_message = f"File {filename} uploaded successfully."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(response_message)))
            self.end_headers()
            self.wfile.write(response_message.encode())

        except Exception as e:
            error_message = f"Server error: {str(e)}"
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(error_message)))
            self.end_headers()
            self.wfile.write(error_message.encode())


     def do_GET(self):
             if self.path == '/downloads':
                 self.serve_download_page()
             elif self.path == '/list-files':
                 self.list_files()
             elif self.path == '/':
                 self.serve_upload_page()
             elif self.path.startswith('/download'):
                         self.handle_file_download()

     def serve_download_page(self):
            try:
                with open("download.html", "rb") as file:
                    content = file.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"404 Not Found: Download page missing.")

     def list_files(self):
            try:
                files = os.listdir(DOWNLOAD_DIR)
                files = [f for f in files if os.path.isfile(os.path.join(DOWNLOAD_DIR, f))]

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(files).encode())
            except Exception as e:
                self.send_error(500, f"Server error: {str(e)}")


     def serve_upload_page(self):
            try:
                with open(HTML_FILE, "rb") as file:
                    content = file.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"404 Not Found: HTML file missing.")
     def handle_file_download(self):
         try:
                     query_components = parse_qs(self.path.split('?', 1)[1])
                     file_name = query_components.get('file_name', [None])[0]

                     if not file_name:
                         self.send_error(400, "Missing file name parameter.")
                         return

                     file_path = os.path.join(DOWNLOAD_DIR, file_name)

                     if not os.path.isfile(file_path):
                         self.send_error(404, f"File {file_name} not found.")
                         return

                     with open(file_path, 'rb') as f:
                         file_content = f.read()

                     self.send_response(200)
                     self.send_header('Content-Type', 'application/octet-stream')
                     self.send_header('Content-Disposition', f'attachment; filename={file_name}')
                     self.send_header('Content-Length', str(len(file_content)))
                     self.end_headers()
                     self.wfile.write(file_content)
         except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")\



def run_server():
    PORT = 8000
    server = HTTPServer(('0.0.0.0', PORT), FileUploadHandler)
    print(f"Server started at http://{get_ip()}:{PORT}")
    server.serve_forever()

def get_ip():
           s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
           try:
               # doesn't even have to be reachable
               s.connect(('10.255.255.255', 1))
               IP = s.getsockname()[0]
           except:
               IP = '127.0.0.1'
           finally:
               s.close()
           return IP

if __name__ == "__main__":
    run_server()
