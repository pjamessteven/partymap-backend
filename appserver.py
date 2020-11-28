"""
appserver.py
- creates an application instance and runs the dev server
"""

if __name__ == '__main__':
    from pmapi.application import create_app
    app = create_app()
    app.run(host='192.168.1.105')
