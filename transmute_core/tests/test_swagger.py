import swagger_schema
from transmute_core import (
    default_context, describe, annotate,
    TransmuteFunction
)
from transmute_core.swagger import (
    generate_swagger_html, get_swagger_static_root,
    SwaggerSpec
)


def test_generate_swagger():
    swagger_static_root = "/statics/_swagger"
    swagger_json_url = "/swagger.json"
    body = generate_swagger_html(swagger_static_root, swagger_json_url)
    assert swagger_static_root in body
    assert swagger_json_url in body


def test_get_swagger_static_root():
    assert "static" in get_swagger_static_root()


def test_swagger_definition_generation():
    """
    swagger routes should be ablo to generate a proper
    spec.
    """
    routes = SwaggerSpec()
    assert routes.swagger_definition() == {
        "info": {"title": "example", "version": "1.0"},
        "paths": {},
        "swagger": "2.0",
    }


def test_swagger_transmute_func(transmute_func):
    """
    swagger routes should be ablo to generate a proper
    spec.
    """
    routes = SwaggerSpec()
    routes.add_func(transmute_func, default_context)
    assert routes.swagger_definition() == {
        "info": {"title": "example", "version": "1.0"},
        "paths": {
            "/api/v1/multiply": transmute_func.get_swagger_path(default_context).to_primitive(),
        },
        "swagger": "2.0",
    }


def test_multiple_response_types(response_transmute_func):
    """ multiple response types should be indicated as such in
    the swagger documentation.
    """
    routes = SwaggerSpec()
    routes.add_func(response_transmute_func, default_context)
    definition = routes.swagger_definition()
    path = definition["paths"]["/api/v1/create_if_authorized/"]
    responses = path["get"]["responses"]
    assert responses["201"] == swagger_schema.Response({
        "description": "",
        "schema": {"type": "boolean"},
        "headers": {
            "location": {"type": "string"}
        }
    }).to_primitive()
    assert responses["401"] == swagger_schema.Response({
        "description": "unauthorized",
        "schema": {"type": "string"}
    }).to_primitive()
    assert "200" not in responses
    assert "400" in responses


def test_swagger_add_path(transmute_func):
    """
    add_path should add the specified path to the main swagger object.
    """
    routes = SwaggerSpec()
    swagger_path = transmute_func.get_swagger_path(default_context)
    for p in transmute_func.paths:
        routes.add_path(p, swagger_path)
    assert routes.swagger_definition() == {
        "info": {"title": "example", "version": "1.0"},
        "paths": {
            "/api/v1/multiply": transmute_func.get_swagger_path(default_context).to_primitive(),
        },
        "swagger": "2.0",
    }


def test_basepath_override():
    assert SwaggerSpec().swagger_definition(base_path="dummy_path") == {
        'basePath': 'dummy_path',
        'info': {'title': 'example', 'version': '1.0'},
        'paths': {},
        'swagger': '2.0'
    }


def test_swagger_get_post(transmute_func, transmute_func_post):
    """
    adding different paths of diffrent methods should have both
    present in the spec.
    """
    routes = SwaggerSpec()
    routes.add_func(transmute_func, default_context)
    routes.add_func(transmute_func_post, default_context)
    spec = routes.swagger_definition()
    assert "get" in spec["paths"]["/api/v1/multiply"]
    assert "post" in spec["paths"]["/api/v1/multiply"]

def test_swagger_parameter_description():
    """
    if parameter descriptions are added to a function, they
    should appear in the swagger json.
    """
    LEFT_DESCRIPTION = "the left operand"
    RIGHT_DESCRIPTION = "the right operand"
    RETURN_DESCRIPTION = "the result"

    @describe(paths="/api/v1/adopt",
              parameter_descriptions={
                "left": LEFT_DESCRIPTION,
                "right": RIGHT_DESCRIPTION,
                "return": RETURN_DESCRIPTION
              })
    @annotate({"left": int, "right": int, "return": int})
    def adopt(left, right):
        return left + right

    func = TransmuteFunction(adopt)

    routes = SwaggerSpec()
    routes.add_func(func, default_context)
    spec = routes.swagger_definition()
    description_by_name = {
        "left": LEFT_DESCRIPTION,
        "right": RIGHT_DESCRIPTION
    }
    for param in spec["paths"]["/api/v1/adopt"]["get"]["parameters"]:
        assert description_by_name[param["name"]] == param["description"]
    assert RETURN_DESCRIPTION == spec["paths"]["/api/v1/adopt"]["get"]\
                                   ["responses"]["200"]["schema"]["description"]
