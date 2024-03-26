import math
from google.oauth2.service_account import Credentials
from googlesheet import update_values




area = 5  # km

voice_speed = 12.2 * pow(10, 3)
data1_speed = 64 * pow(10, 3)
data2_speed = 144 * pow(10, 3)
data3_speed = 384 * pow(10, 3)

Rc = 3.84 * pow(10, 6)
dpc = 0.75
Vj_voice = 0.67
Vj_data = 1
ksi = 0.55
Eb_N0_down = 4  # dB
Eb_N0_up = 5  # dB
kTbssF = -102.6

M_erl = 4000




class Bilans:
    def __init__(self, p_nad, g_nad, g_odb, g_sho, fn, fo, g, eb_to_nt, direction):
        self.p_nad = p_nad
        self.g_nad = g_nad
        self.g_odb = g_odb
        self.g_sho = g_sho
        self.fn = fn
        self.fo = fo
        self.g = g
        self.eb_to_nt = eb_to_nt
        self.direction = direction
        


        lmax = p_nad + g_nad + g_odb + g_sho - fn - fo - kTbssF + g - eb_to_nt - 10 * math.log(2, 10)
        print(f"Maksymalne dopuszczalne tłumienie dla łącza ", direction, " : ", lmax, " dB")
        self.lmax = lmax


def db_to_norm(x):
    log = pow(10, x/10)
    return float(log)


# 1. Max capacity of radio interface WCDMA/FDD

M_12_2_down = 1 + ((Rc * dpc) / (voice_speed * Vj_voice)) * (1 / (1 + ksi)) * (1 / db_to_norm(Eb_N0_down))
print("Pojemność max WCDMA w łączu w dół: ", M_12_2_down)
M_12_2_up = 1 + ((Rc * dpc) / (voice_speed * Vj_voice)) * (1 / (1 + ksi)) * (1 / db_to_norm(Eb_N0_up))
print("Pojemność max WCDMA w łączu w górę: ", M_12_2_up)

update_values("B2:B3", [[M_12_2_down],[M_12_2_up]])


# 2. Acceptable capacity

M_acceptable = min(M_12_2_up, M_12_2_down) * 0.8
print("N do tabelki: ", M_acceptable)
# Przyjmij Pb = 2% i odczytaj wartość z tab. Erlanga
Erlang_B_2_percent = 47.8

# 3. Required number of BTSes

Required_BTS = math.floor(M_erl / Erlang_B_2_percent)
Three_Sector_BTS = math.floor(Required_BTS / 2.5)
print("Liczba stacji trójsektorowych: ", Three_Sector_BTS)

update_values("B5:B5", [[Three_Sector_BTS]])

# 4. Arrangement of BTSes

Area_of_simple_cell = pow(area, 2) / Three_Sector_BTS
print("Powierzchnia jednej komórki: ", Area_of_simple_cell)
Cell_Radius = math.sqrt((2 * Area_of_simple_cell) / (3 * math.sqrt(3)))
print("Promień komórki w km: ", Cell_Radius)

update_values("B6:B7", [[Area_of_simple_cell], [Cell_Radius]])
# 5. Propagation attenuation model

# mikrokomórka gdy r < 0.8 km

if (Cell_Radius < 0.8):
    Prop_Att_Model = 148 + 40 * math.log(Cell_Radius, 10)
else:
    Prop_Att_Model = 128.1 + 37.6 * math.log(Cell_Radius, 10)

update_values("B8:B8", [[Prop_Att_Model]])

# 6. Receiver's sensitivity


Pmin = kTbssF + 4 - 10 * math.log((Rc / voice_speed), 10) + (-10 * math.log(0.5, 10)) #  zapytaj o ebnt, góra dół - ruchome czy bazowe
print(f"Czułość odbiorników: ", Pmin, " dB") # zrób w druga strone

# TU POPRAW ^^^



# 7. Energy balance  ZAKŁADAM WSTĘPNIE ŚRODOWISKO MIEJSKIE
#  do zmiany: 1,2,3,5,6

# domyślne w górę: 14, 2, 13, 0, 0, 2, 25, 5
# domyślne w dół: 30, 13, 2, 2, 2, 0, 25, 4

l_max_voice_up_default = Bilans(14, 2, 13, 0, 0, 2, 25, 5, "12,2 kb/s w górę")
l_max_voice_down = Bilans(30, 13, 2, 2, 2, 0, 25, 4, "12,2 kb/s w dół")

l_max_voice_up = Bilans(27, 7, 16, 0, 1, 13, 25, 5, "12,2 kb/s w górę")
l_max_voice_down = Bilans(26, 5, 3, 2, 1, 0, 25, 4, "12,2 kb/s w dół")

# 8. Bilansuj Pnad, Gnad, Godb, Fn, Fo aby wyrównać tłumienia

P_sred = (l_max_voice_up.p_nad + l_max_voice_down.p_nad) / 2
print(f"Średnia moc nadajników dla transmisji sygnałów mowy: ", P_sred, " dB")

# Zapisz przyjęte parametry

# 9 + 10. Pojemność dla różnych typów usług transmisji danych i całkowita dopuszczalna przepływność


def m_data(data_speed):
    print(f"Dla szybkosci TD: ", data_speed / pow(10, 3), "kb/s")
    m_data_down = 1 + ((Rc * dpc) / (data_speed * Vj_data)) * (1 / (1 + ksi)) * (1 / db_to_norm(Eb_N0_down))
    print(f"Pojemność max w łączu w dół: ", m_data_down)
    m_cell_down = m_data_down * 2.5
    m_network_down = Three_Sector_BTS * m_cell_down
    m_data_up = 1 + ((Rc * dpc) / (data_speed * Vj_data)) * (1 / (1 + ksi)) * (1 / db_to_norm(Eb_N0_up))
    print(f"Pojemność max w łączu w górę: ", m_data_up)
    m_cell_up = m_data_up * 2.5
    m_network_up = Three_Sector_BTS * m_cell_up  #  Liczba komórek - 3 sektorowych?
    m_network = min(m_network_up, m_network_down)
    numb_of_channels = 0.8 * m_network
    total_allow_bitrate = numb_of_channels * data_speed
    print(f"Całkowity dostępny bitrate: ", total_allow_bitrate / pow(10, 3), "kb/s")


m_data(data1_speed)
m_data(data2_speed)
m_data(data3_speed)

# 11 Zasięg

l_max_d1_up_default = Bilans(14, 2, 13, 0, 0, 2, 17.8, 3.5, "64 kb/s w górę")  # default: 14, 2, 13, 0, 0, 2, 17.8, 3.5
l_max_d1_down_default = Bilans(30, 13, 2, 2, 2, 0, 17.8, 3, "64 kb/s w dół")  # default: 14, 2, 13, 0, 0, 2, 17.8, 3.5

l_max_d2_up_default = Bilans(14, 2, 13, 0, 0, 2, 14.3, 2.5, "144 kb/s w górę")  # default: 14, 2, 13, 0, 0, 2, 17.8, 3.5
l_max_d2_down_default = Bilans(30, 13, 2, 2, 2, 0, 14.3, 2, "144 kb/s w dół")  # default: 14, 2, 13, 0, 0, 2, 17.8, 3.5

l_max_d3_up_default = Bilans(14, 2, 13, 0, 0, 2, 10, 2, "384 kb/s w górę")  # default: 14, 2, 13, 0, 0, 2, 17.8, 3.5
l_max_d3_down_default = Bilans(30, 13, 2, 2, 2, 0, 10, 1, "384 kb/s w dół")  # default: 14, 2, 13, 0, 0, 2, 17.8, 3.5


l_max_d1_up = Bilans(27, 2, 13, 0, 1, 2.5, 17.8, 3.5, "64 kb/s w górę")  # default: 14, 2, 13, 0, 0, 2, 17.8, 3.5
l_max_d1_down = Bilans(26, 12, 2, 2, 3, 1, 17.8, 3, "64 kb/s w dół")  # default: 14, 2, 13, 0, 0, 2, 17.8, 3.5

l_max_d2_up = Bilans(30, 2, 13, 0, 0, 2, 14.3, 2.5, "144 kb/s w górę")  # default: 14, 2, 13, 0, 0, 2, 17.8, 3.5
l_max_d2_down = Bilans(30, 11, 2, 2, 2.5, 0, 14.3, 2, "144 kb/s w dół")  # default: 14, 2, 13, 0, 0, 2, 17.8, 3.5

l_max_d3_up = Bilans(30, 2, 13, 0, 0, 2, 10, 2, "384 kb/s w górę")  # default: 14, 2, 13, 0, 0, 2, 17.8, 3.5
l_max_d3_down = Bilans(28, 13, 2, 2, 3, 0, 10, 1, "384 kb/s w dół")  # default: 14, 2, 13, 0, 0, 2, 17.8, 3.5

def distance(l, param):
    d = pow(10, ((l - 148) / 40))
    print(f"Promien d dla usługi ", param, " wynosi: ", d)

#  zrób obliczenia dodatkowo dla zasięgu przed zbilansowaniem
 
distance(l_max_d1_up.lmax, "64 kb/s w łączu w górę")
distance(l_max_d1_down.lmax, "64 kb/s w łączu w dół")
distance(l_max_d2_up.lmax, "144 kb/s w łączu w górę")
distance(l_max_d2_down.lmax, "144 kb/s w łączu w dół")
distance(l_max_d3_up.lmax, "384 kb/s w łączu w górę")
distance(l_max_d3_down.lmax, "384 kb/s w łączu w dół")
distance(l_max_voice_up.lmax, "12,2 kb/s w łączu w górę")
distance(l_max_voice_down.lmax, "12,2 kb/s w łączu w dół")

P_sred_64 = (l_max_d1_up.p_nad + l_max_d1_down.p_nad) / 2
print(f"Średnia moc nadajników dla usługi 64 kb/s: ", P_sred, " dB")
P_sred_144 = (l_max_d2_up.p_nad + l_max_d2_down.p_nad) / 2
print(f"Średnia moc nadajników dla usługi 144 kb/s: ", P_sred, " dB")
P_sred_384 = (l_max_d3_up.p_nad + l_max_d3_down.p_nad) / 2
print(f"Średnia moc nadajników dla usługi 384 kb/s ", P_sred, " dB")


#  program Visio do narysowania komórek



