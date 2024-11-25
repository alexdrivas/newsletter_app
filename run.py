from dotenv import load_dotenv
load_dotenv()  # Load environment variables before app creation

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=8080)


# for local 
#if __name__ == '__main__':
  #  app.run(debug=True)