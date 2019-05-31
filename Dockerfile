FROM lgdop/centos6_python2.7.14:git-2.19.1


WORKDIR /clarify_cdc
#ENV https_proxy=http://172.31.133.12:8080
#ENV http_proxy=http://172.31.133.12:8080


RUN virtualenv my27project && source my27project/bin/activate && python --version
RUN pip2.7 install dash \
                dash-html-components \
                dash-core-components \
                datetime \
                pymongo \
                hvac \
                flask \
                gunicorn

COPY . .
RUN mv /usr/bin/git /usr/bin/git_old && cd /usr/bin && ln -s /usr/local/git/bin/git git

EXPOSE 3000

CMD [ "gunicorn", "--bind", "0.0.0.0:3000","--timeout","10000", "cdc:server" ]
