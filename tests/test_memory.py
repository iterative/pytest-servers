def test_memory_fs_clean(tmp_upath_factory):
    mempath1 = tmp_upath_factory.mktemp("memory")
    mempath2 = tmp_upath_factory.mktemp("memory")

    foo = mempath1 / "foo"
    foo.write_text("foo")
    bar = mempath2 / "bar"
    bar.write_text("bar")

    assert (mempath1 / "foo").exists()
    assert (mempath2 / "bar").exists()
    assert not (mempath1 / "bar").exists()
    assert not (mempath2 / "foo").exists()
