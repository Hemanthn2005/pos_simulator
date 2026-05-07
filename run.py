from app import create_app

app = create_app()

if __name__ == "__main__":
    print("=" * 50)
    print("POS Simulator Running")
    print("Login: http://localhost:5000/login")
    print("POS Terminal: http://localhost:5000/")
    print("Dashboard: http://localhost:5000/admin")
    print("Bills History: http://localhost:5000/bills")
    print("=" * 50)
    app.run(debug=True, port=5000)
