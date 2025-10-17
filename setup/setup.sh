# NOTE: Call this using "source"
#	EXAMPLE: `source setup.sh`

# Install packages
conda create -n stocks
conda activate stocks
conda install pytorch -c pytorch-nightly
conda install anaconda::pandas -y
conda install openpyxl -y
conda install pytz -y
conda install scikit-learn -y
conda install requests -y
#conda install onnx -y
conda install pip -y
#conda install flask -y
#pip install --upgrade onnxscript
pip install --upgrade ollama
pip install --upgrade yfinance
pip install --upgrade pandas-market-calendars
#pip install --upgrade newspaper3k
#pip install --upgrade lxml_html_clean
pip install --upgrade streamlit
pip install --upgrade streamlit-scrollable-textbox
pip install --upgrade Authlib
conda clean -a -y

# Create directories needed for program(s)
mkdir stockdata
mkdir logs

clear