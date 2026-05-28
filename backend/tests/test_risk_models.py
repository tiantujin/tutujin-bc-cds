from app import risk_models, schemas


def test_cts5_groups():
    low = risk_models.calculate_cts5(schemas.CTS5Request(age=55, tumor_size_mm=12, histologic_grade=1, positive_nodes=0))
    high = risk_models.calculate_cts5(schemas.CTS5Request(age=55, tumor_size_mm=50, histologic_grade=3, positive_nodes=4))
    assert low.risk_group == "低危"
    assert high.risk_group == "高危"


def test_npi_formula():
    result = risk_models.calculate_npi(schemas.NPIRequest(tumor_size_cm=2, node_stage=1, histologic_grade=2))
    assert result.score == 3.4
    assert result.risk_group == "低危"


def test_rcb_pcr():
    result = risk_models.calculate_rcb(
        schemas.RCBRequest(
            tumor_bed_max_mm=0,
            tumor_bed_second_mm=0,
            cellularity_percent=0,
            dcis_percent=0,
            positive_nodes=0,
            largest_nodal_met_mm=0,
        )
    )
    assert result.risk_group == "RCB-0 / pCR"
