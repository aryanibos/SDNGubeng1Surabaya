from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html', title="Home")

@app.route('/about')
def about():
    return render_template('about.html', title="About")

@app.route('/guru')
def guru():
    return render_template('dataGuru.html', title="Guru")

@app.route('/visimisi')
def visimisi():
    return render_template('visimisi.html', title="Visi & Misi")

@app.route('/gallery')
def gallery():
    return render_template('gallery.html', title="Gallery")

@app.route('/informasi')
def informasi():
    return render_template('berita.html', title="Informasi")

@app.route('/kontak')
def kontak():
    return render_template('kontak.html', title="Kontak")

if __name__ == '__main__':
    app.run(debug=True)
