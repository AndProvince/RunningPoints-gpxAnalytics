import math
import pandas as pd


def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


def calculate_result_rating(points_list):
    """
    Расчет среднего рейтинга на основе пяти лучших результатов.

    Parameters:
    points_list (list): Список очков за гонки.

    Returns:
    float: Средний рейтинг.
    """
    races_count = 5
    if len(points_list) < 5:
        races_count = len(points_list)

    # Сортировка по убыванию и выбор 5 лучших результатов
    top_5_results = sorted(points_list, reverse=True)[:races_count]
    average_rating = sum(top_5_results) / races_count

    return average_rating


def calculate_race_points(row, T_winner, K):
    """
    Расчет очков за гонку.

    Parameters:
    row (DataFrame row): информация о спортмене в формате строки DataFrame
    T_winner (float): Время победителя (в секундах).
    K (float): Коэффициент сложности трассы.

    Returns:
    float: Очки за гонку.
    """
    if T_winner <= 0 or K <= 0:
        raise ValueError("Все входные параметры должны быть положительными числами.")

    # Время спортсмена (в секундах).
    T_runner = get_sec(row['Result_time'])

    P = K * (T_winner / T_runner) * 1000
    return int(P)


def calculate_points(file, K, result_column='Result_time'):
    df = pd.read_csv(file)

    T_winner = get_sec(df.at[0, result_column])

    df['Result_points'] = df.apply(lambda x: calculate_race_points(x, T_winner, K), axis=1)

    return df

def calculate_difficulty_coefficient(distance, elevation_gain_uphill, elevation_gain_downhill, technical_coefficient_uphill, technical_coefficient_downhill):
    """
    Расчет коэффициента сложности трассы.

    Parameters:
    distance (float): Дистанция трассы в километрах.
    elevation_gain_uphill (float): Набор высоты в метрах.
    elevation_gain_downhill (float): Сброс высоты в метрах.
    technical_coefficient_uphill (float): Коэффициент технической сложности (от 0 до 1.5 и выше).
    technical_coefficient_downhill (float): Коэффициент технической сложности (от 0 до 1.5 и выше).

    Returns:
    float: Коэффициент сложности трассы.
    """
    if (distance <= 0
            or elevation_gain_uphill < 0
            or elevation_gain_downhill < 0
            or technical_coefficient_uphill < 0
            or technical_coefficient_downhill < 0):
        raise ValueError("Все параметры должны быть положительными, а технический коэффициент не меньше 0.")

    base_length = 50000 - (elevation_gain_uphill / 10) + (elevation_gain_downhill / 20)
    # Расчет коэффициента сложности с учетом длины дистанции
    K = ((distance / base_length)
         + (elevation_gain_uphill / 1000) * technical_coefficient_uphill
         + (elevation_gain_downhill / 1000) * technical_coefficient_downhill)
    return K


def calculate_competition_coefficient(avg_rating, num_participants):
    """
    Расчет корректирующего множителя уровня конкуренции.

    Parameters:
    avg_rating (float): Средний рейтинг топ-10 участников.
    num_participants (int): Общее количество участников гонки.

    Returns:
    float: Корректирующий множитель уровня конкуренции.
    """
    if avg_rating < 0 or num_participants <= 0:
        raise ValueError("Средний рейтинг должен быть положительным, количество участников должно быть больше нуля.")

    C_comp = (avg_rating / 1000) * math.log(num_participants)
    return C_comp


def calculate_weather_coefficient(weather_condition):
    """
    Расчет множителя для учета погодных условий.

    Parameters:
    weather_condition (str): Описание погодных условий ('normal', 'moderate', 'difficult', 'extreme').

    Returns:
    float: Коэффициент учета погодных условий.
    """
    weather_coefficients = {
        'normal': 1.0,
        'moderate': 1.1,
        'difficult': 1.2,
        'extreme': 1.3
    }

    if weather_condition not in weather_coefficients:
        raise ValueError(
            "Недопустимое значение погодных условий. Используйте: 'normal', 'moderate', 'difficult', 'extreme'.")

    return weather_coefficients[weather_condition]

def calculate_K(distance, elevation_gain_uphill, elevation_gain_downhill, TK_uphill, TK_downhill, weather_condition, avg_rating, num_participants):

    K_base = calculate_difficulty_coefficient(distance, elevation_gain_uphill, elevation_gain_downhill, TK_uphill, TK_downhill)
    C_weather = calculate_weather_coefficient(weather_condition)
    C_comp = calculate_competition_coefficient(avg_rating, num_participants)

    print(f'K: base = {K_base}, weather = {C_weather}, competition = {C_comp}')
    print(f'K final = {K_base * C_weather * C_comp}')

    return K_base * C_weather * C_comp, K_base, C_weather, C_comp

