async def test__success(container, api):
    result = (await api.internal.health()).validate()
    assert result.message == "ok"
