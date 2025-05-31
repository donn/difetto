# Copyright 2025 Mohamed Gaber
#
# Adapted from nix-eda
#
# Copyright 2023 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
{
  lib,
  yosys,
  clang-tools_16,
}:
yosys.stdenv.mkDerivation (finalAttrs: {
  pname = "yosys-difetto";
  version = "0.1.0";
  dylibs = ["difetto"];

  src = ./.;

  buildInputs = [
    yosys
    yosys.python3
  ];

  nativeBuildInputs = [
    clang-tools_16
  ];

  meta = {
    description = "";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux ++ lib.platforms.darwin;
  };
})
