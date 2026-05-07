from app import create_app

app = create_app()

if __name__ == "__main__":
    print("✅ POS Simulator running at http://localhost:5000")
    print("📊 Admin Dashboard at http://localhost:5000/admin")
    app.run(debug=True, port=5000)
