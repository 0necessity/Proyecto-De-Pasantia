from pagina import create_app
app = create_app()


if __name__ == "__main__":
    # Recuerda ponerlo en False cuando lo entregues (De otra manera los errorhandlers no funcionan)
    app.run(debug=True)
