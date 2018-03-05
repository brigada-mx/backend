from db.map.models import Establishment
from db.map.models import Donor


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
