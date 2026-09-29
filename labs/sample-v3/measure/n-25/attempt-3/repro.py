import sys
from typing import List

from pydantic import AliasChoices, AliasGenerator, BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

my_validation_alias = lambda x: AliasChoices(x.replace('_', '-'), x)  # validation_alias_b


class SubModel(BaseModel):
    sub_list: List[str] = Field(default_factory=list, description="A list argument")
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=my_validation_alias))


class MySettings(BaseSettings):
    sub_model: SubModel = Field(SubModel())

    model_config = SettingsConfigDict(
        cli_parse_args=True,
        env_nested_delimiter="__",
        alias_generator=AliasGenerator(validation_alias=my_validation_alias),
    )


sys.argv = ["test_config.py", "--sub-model.sub-list=a,b,c"]
print(MySettings())
