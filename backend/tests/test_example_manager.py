import pytest
from app.core.example_manager import (
    ExampleManager,
    get_all_examples,
    get_example,
    get_examples_by_category,
    EXAMPLES,
)
from app.models.schemas import ExampleItem, ProcessCard, Operation


class TestExampleManagerGetAll:
    def setup_method(self):
        self.manager = ExampleManager()

    def test_returns_all_examples(self):
        result = self.manager.get_all_examples()
        assert len(result) == len(EXAMPLES)

    def test_each_example_has_required_keys(self):
        for ex in self.manager.get_all_examples():
            assert 'id' in ex
            assert 'name' in ex
            assert 'description' in ex
            assert 'category' in ex
            assert 'card_data' in ex
            assert 'operations_data' in ex


class TestExampleManagerGetById:
    def setup_method(self):
        self.manager = ExampleManager()

    def test_get_existing_example(self):
        result = self.manager.get_example_by_id(1)
        assert result is not None
        assert result['id'] == 1

    def test_get_nonexistent_example(self):
        result = self.manager.get_example_by_id(999)
        assert result is None

    def test_get_each_example(self):
        for ex in EXAMPLES:
            result = self.manager.get_example_by_id(ex['id'])
            assert result is not None
            assert result['name'] == ex['name']


class TestExampleManagerGetByCategory:
    def setup_method(self):
        self.manager = ExampleManager()

    def test_filter_by_category(self):
        result = self.manager.get_examples_by_category("铣削")
        assert all(ex['category'] == "铣削" for ex in result)
        assert len(result) >= 1

    def test_filter_by_drilling_category(self):
        result = self.manager.get_examples_by_category("钻孔")
        assert all(ex['category'] == "钻孔" for ex in result)

    def test_empty_category_returns_all(self):
        result = self.manager.get_examples_by_category("")
        assert len(result) == len(EXAMPLES)

    def test_nonexistent_category(self):
        result = self.manager.get_examples_by_category("不存在的分类")
        assert result == []


class TestToExampleItem:
    def setup_method(self):
        self.manager = ExampleManager()

    def test_converts_to_example_item(self):
        data = EXAMPLES[0]
        item = self.manager.to_example_item(data)
        assert isinstance(item, ExampleItem)
        assert item.id == data['id']
        assert item.name == data['name']
        assert isinstance(item.card_data, ProcessCard)
        assert len(item.operations_data) == len(data['operations_data'])

    def test_all_examples_convertible(self):
        for data in EXAMPLES:
            item = self.manager.to_example_item(data)
            assert isinstance(item, ExampleItem)


class TestConvenienceFunctions:
    def test_get_all_examples_returns_list(self):
        result = get_all_examples()
        assert isinstance(result, list)
        assert len(result) == len(EXAMPLES)
        assert all(isinstance(item, ExampleItem) for item in result)

    def test_get_example_existing(self):
        result = get_example(1)
        assert isinstance(result, ExampleItem)
        assert result.id == 1

    def test_get_example_nonexistent(self):
        result = get_example(999)
        assert result is None

    def test_get_examples_by_category(self):
        result = get_examples_by_category("铣削")
        assert isinstance(result, list)
        assert all(isinstance(item, ExampleItem) for item in result)

    def test_get_examples_by_category_empty(self):
        result = get_examples_by_category("")
        assert len(result) == len(EXAMPLES)
