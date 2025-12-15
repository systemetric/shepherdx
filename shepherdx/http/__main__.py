from shepherdx.http import ShepherdHttp

if __name__ == "__main__":
    shepherd_http = ShepherdHttp("0.0.0.0", 8080)
    shepherd_http.run()

