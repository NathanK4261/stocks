# NOTE: Call this using "source"
#	EXAMPLE: `source setup.sh`
conda create -n stocks
conda activate stocks
conda install pytorch -c pytorch-nightly
conda install anaconda::pandas -y
conda install openpyxl -y
conda install pytz -y
conda install scikit-learn -y
conda install requests -y
conda install onnx -y
conda install pip -y
conda install flask -y
pip install --upgrade onnxscript
pip install --upgrade yfinance
pip install --upgrade ollama
#pip install --upgrade newspaper3k
#pip install --upgrade lxml_html_clean
conda clean -a -y
clear