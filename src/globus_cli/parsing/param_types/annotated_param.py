import click


class AnnotatedParamType(click.ParamType):
    def get_type_annotation(self, param: click.Parameter) -> type:
        raise NotImplementedError
