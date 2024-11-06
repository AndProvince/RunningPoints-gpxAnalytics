from flask import Flask, request, render_template, session, redirect, url_for, send_from_directory
import os
import gpxpy
import utilsRacePoints

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # для использования сессий
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

# Создать папки uploads и results, если они еще не существуют
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(RESULT_FOLDER):
    os.makedirs(RESULT_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def index():
    previous_file = session.get('previous_file')
    results = None

    if request.method == 'POST':
        if 'gpx_file' in request.files:
            gpx_file = request.files['gpx_file']
            if gpx_file and gpx_file.filename != '':
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], gpx_file.filename)
                gpx_file.save(file_path)
                session['previous_file'] = gpx_file.filename  # Сохраняем имя файла в сессии
                previous_file = session.get('previous_file')
            else:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], previous_file)

        TK_uphill = float(request.form['TK_uphill'])
        TK_downhill = float(request.form['TK_downhill'])
        weather_condition = request.form['weather_condition']
        avg_rating = float(request.form['avg_rating'])
        num_participants = int(request.form['num_participants'])

        if file_path:
            gpx = gpxpy.parse(open(file_path, 'r'))
            elevation_gain_uphill = gpx.get_uphill_downhill().uphill
            elevation_gain_downhill = gpx.get_uphill_downhill().downhill
            distance = gpx.get_points_data()[-1].distance_from_start

            K_final, K_base, C_weather, C_comp = utilsRacePoints.calculate_K(
                distance, elevation_gain_uphill, elevation_gain_downhill,
                TK_uphill, TK_downhill, weather_condition, avg_rating, num_participants
            )

            results = {
                'K_base': f'{K_base:.3f}',
                'C_weather': f'{C_weather:.3f}',
                'C_comp': f'{C_comp:.3f}',
                'K_final': f'{K_final:.3f}'
            }

    return render_template('index.html', results=results, previous_file=previous_file)

@app.route('/reset', methods=['GET'])
def reset():
    # Очистка сохраненного файла и сессии
    session.pop('previous_file', None)
    return redirect(url_for('index'))

@app.route('/upload_results', methods=['POST'])
def upload_results():
    if 'uploadFile' in request.files:
        # Обработка файла
        file = request.files['uploadFile']
        if file and file.filename != '':
            file_path = os.path.join(app.config['RESULT_FOLDER'], file.filename)
            file.save(file_path)

            K_final = float(request.form['K_final'])

            result_df = utilsRacePoints.calculate_points(file_path, K_final)

            # Очистка всех строк и столбцов от лишних символов
            result_df = result_df.map(lambda x: str(x).strip() if isinstance(x, str) else x)

            result_df.to_csv(file_path)

        # Pass the DataFrame to a template for display
        return render_template('results_table.html',
                               tables=result_df.to_html(classes='table table-striped table-bordered', index=False),
                               file=file.filename)


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
