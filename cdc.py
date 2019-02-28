#!/usr/local/bin/python2.7
import dash
from dash.dependencies import Input, Output, Event, State
import dash_core_components as dcc
import dash_html_components as html
from flask import Flask
import hvac
#from pandas_datareader import data as web
#from datetime import datetime as dt
import re
import os
from pymongo import MongoClient
import subprocess
import datetime
import sys
#import pymongo
vault_token=subprocess.Popen('cat /run/secrets/clarify-vault-token', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
os.environ['VAULT_TOKEN']=vault_token.strip()
os.environ['no_proxy']='vault'
os.environ['VAULT_URL']='http://vault:8200'
client = hvac.Client()
client = hvac.Client(
 url=os.environ['VAULT_URL'],
 token=os.environ['VAULT_TOKEN']
)

clarify_mongo_user=client.read('lg-bss-clarify/mongo-creds')['data']['mongo-user']
clarify_mongo_pwd=client.read('lg-bss-clarify/mongo-creds')['data']['mongo-pwd']

gitlab_user=client.read('lg-bss-clarify/orchadop-creds')['data']['orchadop-user']
gitlab_pwd=client.read('lg-bss-clarify/orchadop-creds')['data']['orchadop-pwd']

connection=MongoClient('mongodb://'+clarify_mongo_user+':'+clarify_mongo_pwd+'@mongodb:27017/libertyglobal-bss-clarify?ssl=false')
db=connection['libertyglobal-bss-clarify']

server = Flask(__name__)
#table data style
td_style={'padding-top':'10px', 'padding-bottom':'10px','padding-left': '10px','padding-right': '10px','color':'#1A5276'}
#table heading style
th_style={'padding-top':'10px', 'padding-bottom':'10px','padding-left': '10px','padding-right': '10px','color':'#BA4A00'}

app = dash.Dash(__name__,url_base_pathname='/cdc/',server=server)
app.config.supress_callback_exceptions=True  #It is set to suppress the exception that is generated while assigning callbacks to components that are not in the initial layout but are generated by other callbacks
#server = app.server
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
#This key value pair is for loading the 2 dropdowns AAplication Name and Environment
#Key is for Application name and Value is for Environment
affiliate_list=['AT','CH','CZ','NL','RO']

def cdc(rm_to_be_sent, rm_to_be_removed):
  print "Entered CDC function"
  remove_us_dict={}
  send_us_dict={}
  os.system('rm -rf *-'+country)
  os.system('git clone https://'+gitlab_user+':'+gitlab_pwd+'@devops.upc.biz/gitlab/LibertyGlobal/cbbatch-'+country+'.git')
  os.system('git clone https://'+gitlab_user+':'+gitlab_pwd+'@devops.upc.biz/gitlab/LibertyGlobal/cbform-'+country+'.git')
  os.system('git clone https://'+gitlab_user+':'+gitlab_pwd+'@devops.upc.biz/gitlab/LibertyGlobal/globals-'+country+'.git')
  # this for loop is to generate file lists of sending and removing rms
  for each_repo in ['cbbatch-'+country, 'cbform-'+country, 'globals-'+country]:
    sending_file_list=[]
    removing_file_list=[]
    os.chdir(os.environ['PWD']+'/'+each_repo)
    print os.getcwd()
    print "Entered repo " + each_repo
    sending_cmd = "git log --all --no-merges -i --grep="+rm_to_be_sent+" --date-order | grep '^commit '| awk '{print $2}'"
    print sending_cmd
    sending_commit_list=filter(None, subprocess.Popen(sending_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].split('\n'))
    print "sending commit list"
    print sending_commit_list
    for each_commit in sending_commit_list:
      tagged_file_cmd = "git diff-tree --no-commit-id --name-only -r "+each_commit
      untagged_file_cmd="git diff-tree --diff-filter=D --no-commit-id --name-only -r "+each_commit
      sending_file_list.extend(filter(None, subprocess.Popen(tagged_file_cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].split('\n')))
      sending_file_list=list(set(sending_file_list))
      [ sending_file_list.remove(D_file) for D_file in filter(None, subprocess.Popen(untagged_file_cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].split('\n')) if D_file in sending_file_list ]
    removing_cmd = "git log --all --no-merges -i --grep="+rm_to_be_removed+" --date-order | grep '^commit '| awk '{print $2}'"
    print removing_cmd
    removing_commit_list=filter(None, subprocess.Popen(removing_cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].split('\n'))
    print "removing commit list : " + str(removing_commit_list)
    for each_commit in removing_commit_list:
      tagged_file_cmd = "git diff-tree --no-commit-id --name-only -r "+each_commit
      untagged_file_cmd="git diff-tree --diff-filter=D --no-commit-id --name-only -r "+each_commit
      removing_file_list.extend(filter(None, subprocess.Popen(tagged_file_cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].split('\n')))
      removing_file_list=list(set(removing_file_list))
      [ removing_file_list.remove(D_file) for D_file in filter(None, subprocess.Popen(untagged_file_cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].split('\n')) if D_file in removing_file_list ]
  # this for loop is to revert the changes for each file
    print "sending file list : " + str(sending_file_list)
    print "remove file list : " + str(removing_file_list)
    flag=False
    for each_sending_file in sending_file_list:
      if each_sending_file in removing_file_list:
        #remove_commit_cmd="git log --all --no-merges --format='%h %s' "+each_sending_file+" | grep "+rm_to_be_removed+" | head -1 | awk -F' ' '{print $1}'"
        #print remove_commit_cmd
        #remove_commit_sha=subprocess.Popen(remove_commit_cmd,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0]
        #print "removing rm's latest commit = "+ remove_commit_sha
        remove_us_list=coll_handler.find({'RM_ID.'+rm_to_be_removed : {'$exists' : True}}, {'_id' : 1})
        get_us_by_modified_datewise="git branch -a --sort=-committerdate | awk -F'origin/' '{print $NF}' | uniq"
        modified_datewise_us=subprocess.Popen(get_us_by_modified_datewise,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0]
        modified_datewise_us_list=list(set(modified_datewise_us.strip().splitlines()))
        for each_us_dict in remove_us_list:
          for datewise_git_branch in modified_datewise_us_list:
            if datewise_git_branch.find(each_us_dict['_id']) > -1:
              remove_us_dict[modified_datewise_us_list.index(datewise_git_branch)]=each_us_dict['_id']
        removable_us=remove_us_dict[min(remove_us_dict.keys())]            
        removing_rm_story_cmd="git for-each-ref --sort=-committerdate refs/remotes/origin | grep "+removable_us+" | head -1 | awk -F'origin/' '{print $NF}'"
        print removing_rm_story_cmd
        removing_rm_branch=subprocess.Popen(removing_rm_story_cmd,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].strip()
        print "removing rm branch - "+ removing_rm_branch
        
        #######
        send_us_list=coll_handler.find({'RM_ID.'+rm_to_be_sent : {'$exists' : True}}, {'_id' : 1})
        get_us_by_modified_datewise="git branch -a --sort=-committerdate | awk -F'origin/' '{print $NF}' | uniq"
        modified_datewise_us=subprocess.Popen(get_us_by_modified_datewise,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0]
        modified_datewise_us_list=list(set(modified_datewise_us.strip().splitlines()))
        for each_us_dict in send_us_list:
          for datewise_git_branch in modified_datewise_us_list:
            if datewise_git_branch.find(each_us_dict['_id']) > -1:
              send_us_dict[modified_datewise_us_list.index(datewise_git_branch)]=each_us_dict['_id']
        sending_us=send_us_dict[min(send_us_dict.keys())]            
        sending_rm_story_cmd="git for-each-ref --sort=-committerdate refs/remotes/origin | grep "+sending_us+" | head -1 | awk -F'origin/' '{print $NF}'"
        print sending_rm_story_cmd
        sending_rm_branch=subprocess.Popen(sending_rm_story_cmd,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].strip()
        print "sending rm branch - "+ sending_rm_branch
        sending_tagged_commit_cmd="git for-each-ref --sort=-committerdate refs/remotes/origin | grep "+sending_rm_branch+" | awk -F' ' '{print $1}'"
        sending_tagged_commit_sha=subprocess.Popen(sending_tagged_commit_cmd,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0]
        #######
        
        # DE-CONSOLIDATION begins
        os.system('git checkout '+sending_rm_branch.strip())
        os.system('git config merge.conflictstyle diff3')
        existing_tag_of_sending_rm=subprocess.Popen("git tag --sort=-taggerdate --points-at "+sending_tagged_commit_sha.strip()+" | head -1", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0]
        file_specific_remove_commit_cmd="git log --no-merges --format='%h %s' "+each_sending_file+" | grep "+rm_to_be_removed+" | awk -F' ' '{print $1}'"
        file_specific_remove_sha_msg_cmd="git log --no-merges --format='%s' "+each_sending_file+" | grep "+rm_to_be_removed
        file_specific_send_commit_cmd="git log --no-merges --format='%h %s' "+each_sending_file+" | grep "+rm_to_be_sent+" | awk -F' ' '{print $1}'"
        file_specific_remove_commit_list=subprocess.Popen(file_specific_remove_commit_cmd,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].splitlines()
        file_specific_remove_sha_msg_list=subprocess.Popen(file_specific_remove_sha_msg_cmd,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].splitlines()
        commit_sha_msg_dict=dict(zip(file_specific_remove_commit_list,file_specific_remove_sha_msg_list))
        file_specific_send_commit_list=subprocess.Popen(file_specific_send_commit_cmd,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].splitlines()
        #execute revert commands to deconsolidate
        for each_commit in file_specific_remove_commit_list:
          revert_cmd='git revert --no-commit '+each_commit
          git_revert_cmd_output=subprocess.Popen(revert_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()[1]
          print git_revert_cmd_output
          each_commit_msg=commit_sha_msg_dict[each_commit].strip()
          fp=open(each_sending_file, 'r')
          big_string=fp.read()
          fp.close()
          print each_commit +':'+ each_commit_msg+'$'
          str_file_list=re.split(r'(<{7} HEAD(\n.*?)+\|{7} '+each_commit+r'\.\.\. '+each_commit_msg+r'(\n.*?)+\={7}(\n.*?)+>{7} parent of '+each_commit+r'\.\.\. '+each_commit_msg+r')', big_string)
          #print str_file_list
          print "number of patterns observed - "+str(len(str_file_list))
          if git_revert_cmd_output.find('conflicts') > -1:
            print "Started working on the conflicts resolution"
            for each_match in re.finditer(r'(<{7} HEAD(\n.*?)+\|{7} '+each_commit+r'\.\.\. '+each_commit_msg+r'(\n.*?)+\={7}(\n.*?)+>{7} parent of '+each_commit+r'\.\.\. '+each_commit_msg+r')', big_string):
              if each_match.group() in str_file_list:
                print "working with patterns is started in iterative manner"
                match_index=str_file_list.index(each_match.group())
                ours_obj=re.search(r'\<{7} HEAD(.*?\n)+\|{7}',str_file_list[match_index])
                if ours_obj:
                  print "Found Code Section in Ours"
                  iterator_index=ours_line_index=-1
                  ours_iterator_index=rev_iterator_index=rev_line_index=ours_rev_line_index=-1
                  ours_section=ours_obj.group()
                  ours_code=ours_section.lstrip('<<<<<<< HEAD').rstrip('|||||||')
                  ours_code_lines=ours_code.splitlines()
                  ours_code_lines=[value for value in ours_code_lines if value.strip() != '' ]
                  revert_obj=re.search(r'(\|{7} '+each_commit+r'\.\.\. (.*?\n)+\={7})',str_file_list[match_index])
                  if revert_obj:
                    print "Found the code to be reverted"
                    to_be_reverted_section=revert_obj.group()
                    to_be_reverted_code=to_be_reverted_section.lstrip(r'||||||| '+each_commit+r'... '+each_commit_msg+r')').rstrip('=======')
                    theirs_obj=re.search(r'(\={7}(\n.*?)+\>{7})',str_file_list[match_index])
                    to_be_reverted_code_lines=to_be_reverted_code.splitlines()
                    to_be_reverted_code_lines=[value for value in to_be_reverted_code_lines if value.strip() != '' ]
                    for each_ours_line in ours_code_lines:
                      if each_ours_line.find(to_be_reverted_code_lines[0]) > -1:
                        ours_line_index=ours_code_lines.index(each_ours_line)
                        iterator_index=ours_line_index
                        print "match_found at - " + str(ours_line_index)
                        break
                    seq_counter=0
                    if iterator_index > -1:
                      print str(iterator_index) + " - after condition"
                      for each_rev_line in to_be_reverted_code_lines:
                        if iterator_index < len(ours_code_lines):
                          if ours_code_lines[iterator_index].find(each_rev_line.strip()) > -1:
                            iterator_index=iterator_index+1
                            seq_counter=seq_counter+1
                          else:
                            print "rev lines are not in sequence"
                            break
                      print str(seq_counter)+" - before condition"
                      print len(to_be_reverted_code_lines)
                      print to_be_reverted_code_lines
                    if seq_counter == len(to_be_reverted_code_lines):
                      print str(seq_counter)+" - after condition"
                      ours_code_lines_first_part=ours_code_lines[0:ours_line_index]
                      if len(ours_code_lines) > ours_line_index:
                        ours_code_lines_second_part=ours_code_lines[ours_line_index+seq_counter:]
                        ours_code_lines_first_part.extend(ours_code_lines_second_part)
                        temp_ours_code='\n'.join(ours_code_lines_first_part)
                      if theirs_obj:
                        print "entered into theirs"
                        theirs_section=theirs_obj.group()
                        theirs_code=theirs_section.lstrip('=======').rstrip('>>>>>>>')
                        theirs_code_lines=theirs_code.splitlines()
                        theirs_code_lines=[value for value in theirs_code_lines if value.strip() != '' ]
                        print "length of theirs " + str(len(theirs_code_lines))
                        if len(theirs_code_lines) > 0:
                          for each_theirs_line in theirs_code_lines:
                            for each_rev_line in to_be_reverted_code_lines:
                              if each_rev_line.find(each_theirs_line.strip()) > -1:
                                rev_line_index=to_be_reverted_code_lines.index(each_rev_line)
                                rev_iterator_index=rev_line_index
                                print " theirs match_found at - " + str(rev_line_index)
                                break
                            for each_ours_line in ours_code_lines:
                              if each_ours_line.find(each_theirs_line.strip()) > -1:
                                ours_rev_line_index=ours_code_lines.index(each_ours_line)
                                ours_iterator_index=ours_rev_line_index
                                print "theirs match_found at - " + str(ours_rev_line_index)
                                break
                            if rev_iterator_index > -1 and ours_iterator_index > -1:
                              #break
                              print each_theirs_line
                              if temp_ours_code.find(each_theirs_line.strip())== -1:
                                ours_code_lines_first_part.append(each_theirs_line)
                            elif rev_iterator_index == -1 and ours_iterator_index == -1:
                              print each_theirs_line
                              ours_code_lines_first_part.append(each_theirs_line)
                        #rev_seq_counter=0
                        #theirs_temp_list=[]
                        #if rev_iterator_index > -1 and ours_rev_line_index > -1:
                        #  print "theirs count is "+ str(rev_iterator_index) + " - after condition"
                          #for each_theirs_line in theirs_code_lines:
                          #  if rev_iterator_index < len(to_be_reverted_code_lines) and ours_rev_line_index < len(ours_code_lines):
                          #    if to_be_reverted_code_lines[rev_iterator_index].find(each_theirs_line) > -1 and ours_code_lines[ours_iterator_index].find(each_theirs_line) > -1:
                          #      rev_iterator_index=rev_iterator_index+1
                          #      ours_iterator_index=ours_iterator_index+1
                          #      rev_seq_counter=rev_seq_counter+1
                          #      if not temp_ours_code.find(each_theirs_line) > -1:
                          #        theirs_temp_list.append(each_theirs_line)
                          #    else:
                          #      print "theirs lines are not in sequence"
                          #print str(rev_seq_counter)+" - before theirs condition"
                          #print len(theirs_code_lines)
                          #print theirs_code_lines
                        #if rev_seq_counter > 0:
                        #  print "rev count is " +str(rev_seq_counter)+" - after condition"
                        #  ours_code_lines_first_part.extend(theirs_code_lines)
                      ours_code='\n'.join(ours_code_lines_first_part)
                      str_file_list[match_index]=ours_code.strip()
                    else:
                      print "Nothing to be reverted"
                      str_file_list[match_index]=ours_code.strip()
                    print "Code Reversion is finished"
          file_str='\n'.join(str_file_list)
          fp=open(each_sending_file,'w')
          fp.writelines(file_str)
          fp.close()
          print"Code is ready to for git add"
          os.system('git add '+each_sending_file)
          flag=True
    if flag:
      os.system('git config --global user.email "libertyglobal-bss-clarify-internal@accenture.com"')
      os.system('git config --global user.name "LibertyGlobal-BSS-Clarify Workspace Internal User"')
      sha_msg='"De-consolidating '+rm_to_be_removed[3:]+' for '+rm_to_be_sent+'"'
      os.system('git commit -m '+sha_msg)
      #cmd="git log --grep="+sha_msg+" --date-order | grep '^commit '| awk '{print $2}' | head -1"
      #sha_msg_commit=subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].strip()
      os.system('git push origin '+sending_rm_branch)
      # Creating New Tag for De-Consolidated Code based on the old tag
      if existing_tag_of_sending_rm.find('.') > 0:
        latest_tag_of_sending_rm=existing_tag_of_sending_rm.rsplit('.',1)[0]+'.'+str(int(existing_tag_of_sending_rm.rsplit('.',1)[1])+1)
        os.system('git tag -a '+latest_tag_of_sending_rm+' -m "Tagging for '+rm_to_be_sent+' to deliver '+sending_rm_branch+'"')
        os.system('git push --tags')
      #Cherry-Picking De-Consolidation Activity onto Master
      sending_rm_HEAD_cmd='git rev-parse HEAD'
      sending_rm_HEAD=subprocess.Popen(sending_rm_HEAD_cmd,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].strip()
      os.system('git stash')
      os.system('git checkout master')
      os.system('git cherry-pick --no-commit -Xtheirs '+sending_rm_HEAD)
      os.system('git commit --allow-empty -m "Cherry-Picked latest commit of '+sending_rm_branch+'"')
      os.system('git push origin master')
      # DECONSOLIDATION ended

      # CONSOLIDATION begins
      rm_to_be_added=rm_to_be_removed
      adding_rm_branch=removing_rm_branch.strip()
      os.system('git checkout '+adding_rm_branch)
      for each_commit in file_specific_send_commit_list:
        if each_commit.strip() != sending_rm_HEAD.strip():
          os.system('git cherry-pick --no-commit -Xours '+each_commit)
        
      con_sha_msg='"Consolidating '+rm_to_be_sent[3:]+' for '+rm_to_be_added+'"'
      os.system('git commit -m '+con_sha_msg)
      os.system('git push origin '+adding_rm_branch)
      removing_commit_cmd="git for-each-ref --sort=-committerdate refs/remotes/origin | grep "+adding_rm_branch+" | awk -F' ' '{print $1}'"
      removing_commit=subprocess.Popen(removing_commit_cmd,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].strip()
      removing_tagged_commit_sha=subprocess.Popen('git rev-parse '+removing_commit+'~1', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].strip()
      print "removing tagged commit sha : "+removing_tagged_commit_sha
      existing_tag_of_adding_rm=subprocess.Popen("git tag --sort=-taggerdate --points-at "+ removing_tagged_commit_sha.strip()+" | head -1", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].strip()
      print "existing tag of adding rm : "+existing_tag_of_adding_rm
      if existing_tag_of_adding_rm.find('.') > 0:
        latest_tag_of_adding_rm=existing_tag_of_adding_rm.rsplit('.',1)[0]+'.'+str(int(existing_tag_of_adding_rm.rsplit('.',1)[1])+1)
        os.system('git tag -a '+latest_tag_of_adding_rm+' -m "Tagging for '+rm_to_be_added+' to deliver '+adding_rm_branch+'"')
        os.system('git push --tags')
      #Cherry-Picking Consolidation Activity on to the Master
      adding_rm_HEAD_cmd='git rev-parse HEAD'
      adding_rm_HEAD=subprocess.Popen(adding_rm_HEAD_cmd,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].strip()
      os.system('git checkout master')
      os.system('git cherry-pick --no-commit -Xtheirs '+adding_rm_HEAD)
      os.system('git commit --allow-empty -m "Cherry-Picked latest commit of '+removing_rm_branch.strip()+'"')
      os.system('git push origin master')
      #Creating New Tag for Consolidated Code based on Old Tag
      os.system('cd ../')
      msg="Deconsolidation and Consolidation is completed Successfully...! :-) "
      print msg
      # CONSOLIDATION ended
    else:
      msg="There are no common components between "+ rm_to_be_sent +" and " + rm_to_be_removed
      os.system('cd ../')
  return msg

def main_func(affiliate, rm_string):
    global country
    global coll_handler
    country=affiliate
    coll_handler=db[country+'-ci']
    os.chdir(os.environ['PWD'])
    rm_time_dict={}
    input_rm_list=rm_string.strip().split()
    for each_rm in input_rm_list:
      try:
        rm_dict=coll_handler.find_one({'RM_ID.'+each_rm : { '$exists' : True }},  {'RM_ID.'+each_rm : 1})
      except Exception as e :
        print e
        print "Please perform CI for this ticket - "+each_rm+", then only CDC tool will work as expected"
        sys.exit(1)
      if not rm_dict is None:
        rm_time_dict[datetime.datetime.strptime(rm_dict['RM_ID'][each_rm]['build_time'], '%Y_%m_%d_%H_%M_%S').ctime()]=each_rm
    print rm_time_dict
    dates_list=rm_time_dict.keys()
    dates_list.sort(key=lambda date: datetime.datetime.strptime(date, '%a %b  %d %H:%M:%S %Y'))
    sorted_dates_list=dates_list
    sorted_rm_list=[rm_time_dict[each_date] for each_date in sorted_dates_list]
    print "Developed Order : "+str(sorted_rm_list)
    print "To be Deployed Order : "+str(input_rm_list)
    cdc_rm_list=[]
    cdc_output_dict={}
    for each_rm in input_rm_list:
      print each_rm
      i=sorted_rm_list.index(each_rm)
      if i != 0:
        temp_dc_list=sorted_rm_list[:i]
        print str(temp_dc_list)+" to be deconsolidated from "+each_rm
        for each_dc_rm in temp_dc_list:
          cdc_output_dict[each_dc_rm+'~'+each_rm]=cdc(each_rm, each_dc_rm)
        sorted_rm_list.remove(each_rm)
        cdc_rm_list.append(each_rm)
    return "\n "+ str(cdc_output_dict)

def perform_build(cdc_rm_list):
        print "RUN ci pipeline for "


#pdb.set_trace()
#Desiging layout of page
app.layout = html.Div([
    #Including local stylesheet
        html.Link(href='/static/cdc_layout_style.css', rel='stylesheet'),
    html.Div([
        html.Img(
        src='/img/Accenture-logo-red.png',
        style={
            'height' : '100%',
            'width' : '12%',
            'display':'inline-block',
            'float':'left',
            'padding-right':'20px'
        }
       ),
        html.Div([
             html.H1(children='CLARIFY',style={'textAlign': 'center','color': '#157DEC'})
           ],style={'padding-left':'400px','display':'inline-block','float':'left'}),
    #html.Br(),
        html.Img(
        src='/img/logo-client-liberty-color.jpg',
        style={
            'height' : '100%',
            'width' : '12%',
            'display':'inline-block',
            'float':'right',
            'padding-right':'20px'
        }
       )],className='head-conatiner'),
    #html.Br(),
        #html.Br(),
    html.Div([
        html.Div([html.H1(children='CODE  {...}',style={'padding-right':'8px','textAlign': 'center','color': '#FF8C00','display':'inline-block'} ),
		html.H1(children='CONSOLIDATION <',style={'textAlign': 'center','color': '#006400','display':'inline-block'} ),
		html.H1(children='> DE-CONSOLIDATION',style={'textAlign': 'center','color': '#A20606','display':'inline-block'} ),
        ],style={'textAlign':'center'}),
    html.Br(),
    html.Br(),
    html.Div(id='Affiliate_temp_store',style={'display':'none'}),
    html.Div(id='rm_ticket_temp_store',style={'display':'none'}),
    dcc.Location(id='url', refresh=False),
    html.Div(id='load_layout'),
    #html.Div(id='cdc_result',style={'textAlign':'center','color':'#6B8E23'})
    ],className='main-container')])

home_page=html.Div([
        html.Table(
        # Header
        children=[

        # Body
            html.Tbody(
                [html.Tr([
                    html.Td('Affiliate',style={'padding-bottom':'10px','padding-right': '30px','textAlign': 'left','color':'#000000','fontSize': 20}),
                    html.Td(children=html.Div(dcc.Dropdown(id='Affiliate',
                                                           options=[{'label': k, 'value': k} for k in affiliate_list],
                                                           style={'color':'#000000','width':'80px','border':'1px solid','borderRadius':'4px','fontWeight':'bold'})),style={'padding-bottom':'10px','padding-left': '10px','padding-right': '40px'})
                    ]),
                html.Tr([
                    html.Td('Patches Deployment Order',style={'padding-bottom':'10px','padding-right': '30px','textAlign': 'left','color':'#000000','fontSize': 20}),
                    html.Td(children=html.Div(dcc.Textarea(id = 'rm-ticket',
                                                                                 placeholder='For Example:         RM-12345 RM-22345',value='',minLength='500px',maxLength='1000px',
                                                             style={'color':'#000000','width':'100px','height':'200px','border':'2px solid','fontSize':18,'fontWeight':'bold'})),style={'padding-bottom':'10px','padding-left': '10px','padding-right': '40px'})
                    ])
                ])
    ],style={
            'margin-left': 'auto',
            'margin-right': 'auto',
            'padding-left': '50px',
            'padding-right': '50px',
            'textAlign': 'left',
            'border':'1px'
            }),
    html.Br(),
    html.Div(id='submit_button'),

        html.Br(),
        html.Br(),
        html.Div(id='display_final_result'),
 ])

build_layout=html.Div(html.Div(html.Div("In Progress...",style={'fontSize':30,'color':'#FFA500'}),id='temp_id'),id='cdc_result',style={'textAlign':'center','color':'#6B8E23','fontSize':15})

build_status_layout=html.Div(html.Div(id='temp_status_id',children=''),id='status',style={'textAlign':'center','color':'#6B8E23','fontSize':20})

@app.callback(
    Output('submit_button','children'),
    [Input('rm-ticket', 'value'),
     Input('Affiliate', 'value' )])
def display_insert_button(rm_ticket,Affiliate):
    if Affiliate:
        if rm_ticket:
            if re.search(r'(RM-[0-9]{5,6}\n{0,}){2,}',rm_ticket):
                return html.Div(html.Button(id='Submit',
                                 n_clicks=0, children = dcc.Link('Submit',href='/cdc/build'),
                                 style={'padding-top':'5px','padding-bottom':'5px','color':'#008080','backgroundColor':'#A9A9A9','width':'85px','borderRadius':'4px'}),style={'padding-left':'465px'})
            else:
                return html.Div('Please Ensure to Provide Proper RM Tickets!!!',style={'padding-left': '425px','textAlign': 'left','color': '#DF0101','fontSize':25})

@app.callback(Output('Affiliate_temp_store','children'),
              [Input('Affiliate','value')])
def store_affiliate(Affiliate):
    return Affiliate

@app.callback(Output('rm_ticket_temp_store','children'),
              [Input('rm-ticket','value')])
def store_rm_ticket(rm_ticket):
    return rm_ticket

@app.callback(Output('cdc_result','children'),
              [Input('temp_id','children')],
              [State('url','pathname'),State('Affiliate_temp_store','children'),State('rm_ticket_temp_store','children')])
def display_cdc_result(temp,path,Affiliate,rm_ticket):
    if path == '/cdc/build':
        if not Affiliate is None:
            #calling cdc main function
            #output=main_func(affiliate=Affiliate.lower(), rm_string=rm_ticket)
            output="Consolidation and De-Consolidation is Completed Successfully..! :-) "
            return html.Div([
                    html.Table(
        # Header
        children=[
            html.Tbody([
                html.Tr([
                    html.Th('Country', style={'padding-top':'10px', 'padding-bottom':'10px','padding-left': '10px','padding-right': '10px','color':'#157DEC'}),
                    html.Td(Affiliate,style={'padding-top':'10px', 'padding-bottom':'10px','padding-left': '10px','padding-right': '10px','color':'#808000'})]),

                html.Tr([
                    html.Th('RM Deployment Order',style={'padding-top':'10px', 'padding-bottom':'10px','padding-left': '10px','padding-right': '10px','color':'#157DEC'}),
                    html.Td(rm_ticket,style={'padding-top':'10px', 'padding-bottom':'10px','padding-left': '10px','padding-right': '10px','color':'#808000'})
                    ])]
                )
    ],style={
            'margin-left': 'auto',
            'margin-right': 'auto',
            'padding-left': '50px',
            'padding-right': '50px',
            'textAlign': 'left',
            }),   
                    html.Br(),
                    html.B(output,style={'fontSize':20}),
                    html.Br(),
                    html.Br(),
                    html.Button(id='Build',
                         n_clicks=0, children = dcc.Link('Build',href='/cdc/build_status'),
                         style={'padding-top':'5px','padding-bottom':'5px','color':'#008080','backgroundColor':'#A9A9A9','width':'85px','borderRadius':'4px'}),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Br(),
					html.Div(html.Button(id='back',
                                 n_clicks=0, children = dcc.Link('Back',href='/cdc/'),
                                 style={'padding-top':'5px','padding-bottom':'5px','color':'#008080','backgroundColor':'#A9A9A9','width':'85px','borderRadius':'4px'}),style={'padding-right':'10px','float':'right'})])
        else:
            return html.Div([html.B("Please go to home page to enter the inputs... "),
                            dcc.Link('Home Page',href='/cdc')],style={'textAlign':'center'})

@app.callback(Output('status','children'),
              [Input('temp_status_id','children')],
              [State('url','pathname'),State('Affiliate_temp_store','children'),State('rm_ticket_temp_store','children')])
def display_build_status_result(temp,path,Affiliate,rm_ticket):
    if path == '/cdc/build_status':
        if not Affiliate is None:
            return html.Div("Build in progress...",style={'fontSize':24,'color':'#FFA500'})
        else:
            return html.Div([html.B("Please go to home page to enter the inputs... "),
                            dcc.Link('Home Page',href='/cdc')],style={'textAlign':'center'})

@app.callback(Output('load_layout', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/cdc' or pathname == '/cdc/':
        return home_page
    elif pathname=='/cdc/build':
        return build_layout
    elif pathname=='/cdc/build_status':
        return build_status_layout

if __name__ == '__main__':
    server.run(debug=True)
