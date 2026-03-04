FROM rocker/r-ver:4.5

LABEL authors="Manuel Schoenberger <manuel.schoenberger@othr.de>"

ENV DEBIAN_FRONTEND noninteractive
ENV LANG="C.UTF-8"
ENV LC_ALL="C.UTF-8"

# Install required packages
#RUN apt-get update && apt-get install -y \
#		wget \
#        python3.10 \
#        python3-pip \
#        texlive-latex-base \
#        texlive-science \
#        texlive-fonts-recommended \
#        texlive-publishers \
#        texlive-bibtex-extra \
#		libcairo2-dev \
#		libxt-dev \
#		libudunits2-dev \
#		libproj15 \
#		libgdal-dev \
#       biber 
		
# Install required packages
RUN apt-get update && apt-get install -y \
		wget \
        python3.10 \
		python3-pip
		
		
# Install R Packages
#RUN R -e "install.packages('ggplot2')"
#RUN R -e "install.packages('ggh4x')"
#RUN R -e "install.packages('ggpmisc')"

#RUN R -e "install.packages('ggrastr')"
#RUN R -e "install.packages('ggpattern')"
#RUN R -e "install.packages('ggfortify')"

#RUN R -e "install.packages('dplyr')"
#RUN R -e "install.packages('forcats')"
#RUN R -e "install.packages('stringr')"

#RUN R -e "install.packages('scales')"
#RUN R -e "install.packages('tidyr')"
#RUN R -e "install.packages('tibble')"
#RUN R -e "install.packages('tikzDevice')"

# Add user
RUN useradd -m -G sudo -s /bin/bash repro && echo "repro:repro" | chpasswd
RUN usermod -a -G staff repro
USER repro

# Add artifacts (from host) to home directory
ADD --chown=repro:repro . /home/repro/vldb26-repro

WORKDIR /home/repro/vldb26-repro

# install python packages
ENV PATH $PATH:/home/repro/.local/bin
RUN pip3 install --user --break-system-packages gurobipy==12.0.2
RUN pip3 install --user --break-system-packages numpy

ENTRYPOINT ["./scripts/run.sh"]
CMD ["bash"]
