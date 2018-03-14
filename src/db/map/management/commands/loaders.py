import csv

from db.map.models import Locality, Establishment, Donor


_denue_load_count = 0


def load_denue(row):
    """Load denue row to DB.
    """
    fields = (
        'denue_id',
        'nom_estab',
        'raz_social',
        'codigo_act',
        'nombre_act',
        'per_ocu',
        'tipo_vial',
        'nom_vial',
        'tipo_v_e_1',
        'nom_v_e_1',
        'tipo_v_e_2',
        'nom_v_e_2',
        'tipo_v_e_3',
        'nom_v_e_3',
        'numero_ext',
        'letra_ext',
        'edificio',
        'edificio_e',
        'numero_int',
        'letra_int',
        'tipo_asent',
        'nomb_asent',
        'tipoCenCom',
        'nom_CenCom',
        'num_local',
        'cod_postal',
        'cve_ent',
        'entidad',
        'cve_mun',
        'municipio',
        'cve_loc',
        'localidad',
        'ageb',
        'manzana',
        'telefono',
        'correoelec',
        'www',
        'tipoUniEco',
        'latitud',
        'longitud',
        'fecha_alta',
    )
    values_dict = {k: v for k, v in zip(fields, row)}
    establishment = Establishment.objects.filter(denue_id=values_dict['denue_id']).first()
    if establishment is None:
        Establishment.objects.create(**values_dict)

    global _denue_load_count
    _denue_load_count += 1
    if _denue_load_count % 1000 == 0:
        print(_denue_load_count)


def load_donors():
    donors = [
        'Fundación Azteca', 'Takeda', 'Banorte', 'Fundación Checo Pérez', 'ENGIE',
        'Volkswagen ', 'Auto Traffic', 'TAG', 'Fundación GIN', 'SEDESO', 'FIBRA 1', 'IPADE',
        'Fundación Gigante', 'Chiesi Farmaceútica', 'WeWork', 'Servicios Caritativos', 'Silvia Galvan'
    ]

    for donor in donors:
        try:
            Donor.objects.create(name=donor)
        except:
            pass


def load_marg_data(file):
    """For loading CONEVAL "rezago social" data.
    """
    with open(file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        for i, row in enumerate(reader):
            if i % 1000 == 0:
                print(i)

            clean = [e.strip() for e in row]
            cvegeo = clean[1].rjust(9, '0')
            analfabet = float(clean[7])
            dropout = float(clean[8])
            noPrimary = float(clean[9])
            noHealth = float(clean[10])
            dirtFloor = float(clean[11])
            noToilet = float(clean[12])
            noPlumb = float(clean[13])
            noDrain = float(clean[14])
            noElec = float(clean[15])
            noWasher = float(clean[16])
            noFridge = float(clean[17])
            margIndex = float(clean[19])
            margGrade = clean[20]

            l = Locality.objects.filter(cvegeo=cvegeo).first()
            if l is None:
                continue
            meta = {
                **l.meta,
                'analfabet': analfabet,
                'dropout': dropout,
                'noPrimary': noPrimary,
                'noHealth': noHealth,
                'dirtFloor': dirtFloor,
                'noToilet': noToilet,
                'noPlumb': noPlumb,
                'noDrain': noDrain,
                'noElec': noElec,
                'noWasher': noWasher,
                'noFridge': noFridge,
                'margIndex': margIndex,
                'margGrade': margGrade,
            }
            l.meta = meta
            l.save()


def reset_marg_data():
    i = 0
    for l in Locality.objects.all():
        i += 1
        if i % 1000 == 0:
            print(i)

        if not l.meta:
            continue

        meta = {}
        attributes = ['destroyed', 'habit', 'notHabit', 'total']
        for a in attributes:
            if a in l.meta:
                meta[a] = l.meta[a]
        l.meta = meta
        l.save()
