__author__ = 'chmoe'

import http.server
import json

SERVER_PORT = 2000

DB_PATH = "db"
DEFAULT_DB_FILE = "default_db.json"

db_dict = {}
db_file = DEFAULT_DB_FILE

class MyHandler(http.server.BaseHTTPRequestHandler):
    def update_db_file(self):
        #print("CURRENT_DATA=" + str(db_dict) + "; type=" + str(type(db_dict)))
        db_serialized = json.dumps(db_dict)

        with open(db_file,'w') as json_data:
            json_data.write(db_serialized)
            #json.dump(json_data, str(db_dict))
            json_data.close()

    def resolve_path_to_object(self, path):
        dict_keys = path.split('/')

        if dict_keys[1] == DB_PATH:
            dict_keys = dict_keys[2:]   # skip first entry, as it is '', and second, as it must be "$DB_PATH"
            data = db_dict

            if dict_keys:
                try:
                    for x in dict_keys:
                        parent_object = data
                        data = data[x]
                except:
                    data = None
                    pass
            else:
                parent_object = None
                x = None

            return [data, parent_object, x]
        else:
            return None

    """
        Sends an error code and a simple body showing the error code
    """
    def send_simple_error(self, error_code):
        self.send_response(error_code)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        self.wfile.write(bytes("error " + str(error_code), 'UTF-8'))

    def do_GET(self):
        #try:
            [data, parent, x] = self.resolve_path_to_object(self.path)

            print("GET data=" + str(data))
            print("GET parent=" + str(parent))

            if data:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes(str(data), 'UTF-8'))
            else:
                self.send_simple_error(404)
        #except:
        #    self.send_simple_error(400)

    def do_PUT(self):
        #try:
            [data, parent, final_key] = self.resolve_path_to_object(self.path)

            print("PUT data=" + str(data))
            print("PUT parent=" + str(parent))

            if data:
                payload_length = int(self.headers['Content-Length'])
                payload = self.rfile.read(payload_length)

                new_object = json.loads(str(payload, 'UTF_8'))
                print ("NEW_OBJECT=" + str(new_object))

                parent[final_key] = new_object
                self.update_db_file()

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes("OK", 'UTF-8'))
            else:
                self.send_simple_error(404)

        #except:
        #    self.send_simple_error(400)


    def do_POST(self):
        #try:
            [data, parent, final_key] = self.resolve_path_to_object(self.path)

            print("POST data=" + str(data))
            print("POST parent=" + str(parent))

            # only allow request if data item does not exist
            # and parent is a dictionary
            if data is None and isinstance(parent, dict):
                payload_length = int(self.headers['Content-Length'])
                payload = self.rfile.read(payload_length)

                new_object = json.loads(str(payload, 'UTF_8'))
                print ("NEW_OBJECT=" + str(new_object))

                parent[final_key] = new_object

                self.update_db_file()

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes("OK", 'UTF-8'))
            else:
                self.send_simple_error(400)

    def do_DELETE(self):
        #try:
            [data, parent, final_key] = self.resolve_path_to_object(self.path)

            print("DELETE data=" + str(data))
            print("DELETE parent=" + str(parent))

            # only allow request if data item does not exist
            # and parent is a dictionary
            if data:
                del parent[final_key]
                self.update_db_file()
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes("OK", 'UTF-8'))
            else:
                self.send_simple_error(400)


if __name__ == '__main__':
    with open(db_file) as json_data:
        db_dict = json.load(json_data)
        json_data.close()
    server_class = http.server.HTTPServer
    httpd = server_class(("localhost", SERVER_PORT), MyHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

#print("hello")