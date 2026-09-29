import sys
from typing import List
from pydantic import Field, AliasChoices, BaseModel, AliasGenerator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

sys.argv = ["test_config.py", "--sub-model.sub-list=a,b,c"]
alias = lambda x: AliasChoices(x.replace('_', '-'), x)

class SubModel(BaseModel):
    sub_list: List[str] = Field(default_factory=list, description="A list argument")
    model_config = ConfigDict(alias_generator=AliasGenerator(validation_alias=alias))

class MySettings(BaseSettings):
    sub_model: SubModel = Field(SubModel())
    model_config = SettingsConfigDict(
        cli_parse_args=True,
        env_nested_delimiter="__",
        alias_generator=AliasGenerator(validation_alias=alias),
    )

print(MySettings())
